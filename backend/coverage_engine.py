from __future__ import annotations

from dataclasses import dataclass
from hashlib import blake2b
from typing import Dict, List, Tuple, Any, Optional

from .coverage_config import CoverageConfig


AXES_ORDER = [
    "price_sensitivity",
    "brand_bias",
    "availability",
    "policy_boundary",
]


@dataclass(frozen=True)
class Scenario:
    domain: str
    behavior: str
    axes: Tuple[Tuple[str, str], ...]  # ((axis_name, bin), ... in AXES_ORDER)

    @property
    def id(self) -> str:
        # Stable ID composed from axis values in fixed order
        parts = [f"{k}={v}" for k, v in self.axes]
        return f"{self.domain}|{self.behavior}|" + "|".join(parts)


def _axis_index_map(taxonomy: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
    idx: Dict[str, Dict[str, int]] = {}
    axes = taxonomy.get("axes", {})
    for a in AXES_ORDER:
        vals = axes.get(a, [])
        idx[a] = {v: i for i, v in enumerate(vals)}
    return idx


def enumerate_scenarios(taxonomy: Dict[str, Any], domain: str, behavior: str) -> List[Scenario]:
    axes = taxonomy["axes"]
    items: List[Scenario] = []
    for ps in axes["price_sensitivity"]:
        for bb in axes["brand_bias"]:
            for av in axes["availability"]:
                for pb in axes["policy_boundary"]:
                    items.append(
                        Scenario(
                            domain=domain,
                            behavior=behavior,
                            axes=tuple(
                                (k, v)
                                for k, v in zip(
                                    AXES_ORDER, [ps, bb, av, pb]
                                )
                            ),
                        )
                    )
    return items


def _matches_filter(sc: Scenario, cond: Dict[str, List[str]]) -> bool:
    # Returns True when sc satisfies all keys present in cond
    for k, allowed in cond.items():
        if not allowed:
            continue
        val = dict(sc.axes).get(k)
        if val not in set(allowed):
            return False
    return True


def _exclude_scenarios(scenarios: List[Scenario], rule: Dict[str, Any]) -> List[Scenario]:
    when = rule.get("when", {}) or {}
    exclude_axes = ((rule.get("exclude") or {}).get("axes")) or {}
    if not exclude_axes:
        return scenarios
    kept: List[Scenario] = []
    for sc in scenarios:
        if when and not _matches_filter(sc, when):
            kept.append(sc)
            continue
        # if any axis in exclude matches, drop
        sc_axes = dict(sc.axes)
        drop = False
        for ax, values in exclude_axes.items():
            if values and sc_axes.get(ax) in set(values):
                drop = True
                break
        if not drop:
            kept.append(sc)
    return kept


def _cap_scenarios(
    scenarios: List[Scenario], rule: Dict[str, Any], taxonomy: Dict[str, Any], seed: int
) -> List[Scenario]:
    cap = rule.get("cap")
    if not isinstance(cap, int) or cap < 1:
        return scenarios
    when = rule.get("when", {}) or {}
    # Partition into matching and non-matching
    matching: List[Scenario] = []
    non_matching: List[Scenario] = []
    for sc in scenarios:
        (matching if _matches_filter(sc, when) else non_matching).append(sc)

    if len(matching) <= cap:
        return scenarios  # nothing to do

    # Deterministic selection of cap scenarios from matching
    idx_map = _axis_index_map(taxonomy)

    def stable_key(sc: Scenario) -> Tuple:
        # 1) axis index order; 2) hash with seed for tie-break
        sc_axes = dict(sc.axes)
        order_tuple = tuple(idx_map[a][sc_axes[a]] for a in AXES_ORDER)
        h = blake2b(
            f"{seed}|{sc.id}".encode("utf-8"), digest_size=8
        ).hexdigest()
        # convert to int for ordering
        return order_tuple + (int(h, 16),)

    selected = sorted(matching, key=stable_key)[:cap]
    # Preserve overall order deterministically by re-sorting all by stable_key, but keeping only selected for matching subset
    selected_ids = {sc.id for sc in selected}
    result: List[Scenario] = []
    # Keep selected from matching (sorted) + all non-matching
    result.extend(sorted(selected, key=lambda sc: sc.id))
    result.extend(non_matching)
    return result


def _applies_to(domain: str, behavior: str, applies: Optional[Dict[str, Any]]) -> bool:
    if not applies:
        return True
    doms = applies.get("domains")
    behs = applies.get("behaviors")
    if doms and domain not in doms:
        return False
    if behs and behavior not in behs:
        return False
    return True


def apply_exclusions(
    taxonomy: Dict[str, Any],
    exclusions: Dict[str, Any],
    domain: str,
    behavior: str,
    seed: int = 42,
) -> List[Scenario]:
    scenarios = enumerate_scenarios(taxonomy, domain, behavior)
    rules: List[Dict[str, Any]] = exclusions.get("rules", [])
    # Apply rules in given order. Process excludes first (rules with 'exclude'), then caps for the same rule if present.
    for rule in rules:
        if not _applies_to(domain, behavior, rule.get("applies")):
            continue
        if rule.get("exclude"):
            scenarios = _exclude_scenarios(scenarios, rule)
        if rule.get("cap"):
            scenarios = _cap_scenarios(scenarios, rule, taxonomy, seed)
    return scenarios


class CoverageEngine:
    def __init__(self, config: Optional[CoverageConfig] = None) -> None:
        self.config = config or CoverageConfig()
        self.taxonomy = self.config.load_taxonomy()
        self.exclusions = self.config.load_exclusions()

    def scenarios_for(self, domain: str, behavior: str, seed: int = 42) -> List[Scenario]:
        return apply_exclusions(self.taxonomy, self.exclusions, domain, behavior, seed)
