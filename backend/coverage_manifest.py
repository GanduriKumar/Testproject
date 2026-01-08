from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

from .coverage_config import CoverageConfig
from .coverage_engine import (
    AXES_ORDER,
    Scenario,
    enumerate_scenarios,
    _exclude_scenarios,
    _cap_scenarios,
)


@dataclass
class RuleBreakdown:
    name: str
    type: str
    removed_exclude: int = 0
    removed_cap: int = 0


@dataclass
class ScenarioRecord:
    id: str
    axes: Dict[str, str]


@dataclass
class PairManifest:
    domain: str
    behavior: str
    raw_total: int
    breakdown: List[RuleBreakdown]
    final_total: int
    scenarios: List[ScenarioRecord]


def _scenario_to_record(sc: Scenario) -> ScenarioRecord:
    return ScenarioRecord(id=sc.id, axes=dict(sc.axes))


def build_pair_manifest(
    taxonomy: Dict[str, Any],
    exclusions: Dict[str, Any],
    domain: str,
    behavior: str,
    seed: int = 42,
) -> PairManifest:
    rules: List[Dict[str, Any]] = exclusions.get("rules", [])
    scenarios = enumerate_scenarios(taxonomy, domain, behavior)
    raw_total = len(scenarios)
    breakdown: List[RuleBreakdown] = []

    for rule in rules:
        applies = rule.get("applies") or {}
        doms = applies.get("domains")
        behs = applies.get("behaviors")
        if doms and domain not in doms:
            continue
        if behs and behavior not in behs:
            continue

        before = len(scenarios)
        removed_exclude = 0
        removed_cap = 0

        if rule.get("exclude"):
            after_excl = _exclude_scenarios(scenarios, rule)
            removed_exclude = before - len(after_excl)
            scenarios = after_excl
            before = len(scenarios)

        if rule.get("cap"):
            after_cap = _cap_scenarios(scenarios, rule, taxonomy, seed)
            removed_cap = before - len(after_cap)
            scenarios = after_cap

        breakdown.append(
            RuleBreakdown(
                name=rule.get("name", "unnamed"),
                type=rule.get("type", "unknown"),
                removed_exclude=removed_exclude,
                removed_cap=removed_cap,
            )
        )

    final_scenarios = scenarios
    return PairManifest(
        domain=domain,
        behavior=behavior,
        raw_total=raw_total,
        breakdown=breakdown,
        final_total=len(final_scenarios),
        scenarios=[_scenario_to_record(sc) for sc in final_scenarios],
    )


def build_manifest(
    taxonomy: Dict[str, Any], exclusions: Dict[str, Any], seed: int = 42
) -> Dict[str, Any]:
    manifest_pairs: List[Dict[str, Any]] = []
    for domain in taxonomy.get("domains", []):
        for behavior in taxonomy.get("behaviors", []):
            pm = build_pair_manifest(taxonomy, exclusions, domain, behavior, seed)
            manifest_pairs.append(
                {
                    "domain": pm.domain,
                    "behavior": pm.behavior,
                    "raw_total": pm.raw_total,
                    "breakdown": [asdict(b) for b in pm.breakdown],
                    "final_total": pm.final_total,
                    "scenarios": [asdict(s) for s in pm.scenarios],
                }
            )
    return {
        "seed": seed,
        "axes_order": AXES_ORDER,
        "pairs": manifest_pairs,
    }


class CoverageManifestor:
    def __init__(self, config: Optional[CoverageConfig] = None) -> None:
        self.config = config or CoverageConfig()
        self.taxonomy = self.config.load_taxonomy()
        self.exclusions = self.config.load_exclusions()

    def build(self, seed: int = 42) -> Dict[str, Any]:
        return build_manifest(self.taxonomy, self.exclusions, seed)

    def get_pair(self, manifest: Dict[str, Any], domain: str, behavior: str) -> Optional[Dict[str, Any]]:
        for p in manifest.get("pairs", []):
            if p.get("domain") == domain and p.get("behavior") == behavior:
                return p
        return None
