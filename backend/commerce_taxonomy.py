from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional


@dataclass
class CommerceTaxonomy:
    version: str
    domain_type: str
    domains: List[str]
    behaviors: List[str]
    axes: Dict[str, List[str]]


@dataclass
class RiskTiers:
    version: str
    strategy: Dict[str, Any]
    risk: Dict[str, Any]


class TaxonomyValidationError(Exception):
    pass


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_taxonomy(path: str | Path) -> CommerceTaxonomy:
    p = Path(path)
    data = _load_json(p)
    required_keys = {"version", "domain_type", "domains", "behaviors", "axes"}
    missing = required_keys - set(data.keys())
    if missing:
        raise TaxonomyValidationError(f"taxonomy missing keys: {sorted(missing)}")
    axes = data.get("axes") or {}
    for axis_name, bins in axes.items():
        if not isinstance(bins, list) or not bins:
            raise TaxonomyValidationError(f"axis '{axis_name}' must have non-empty list of bins")
        for b in bins:
            if not isinstance(b, str) or not b:
                raise TaxonomyValidationError(f"axis '{axis_name}' has invalid bin: {b}")
    return CommerceTaxonomy(
        version=str(data["version"]),
        domain_type=str(data["domain_type"]),
        domains=list(data["domains"]),
        behaviors=list(data["behaviors"]),
        axes=axes,
    )


def load_risk_tiers(path: str | Path, taxonomy: CommerceTaxonomy) -> RiskTiers:
    p = Path(path)
    data = _load_json(p)
    required_keys = {"version", "strategy", "risk"}
    missing = required_keys - set(data.keys())
    if missing:
        raise TaxonomyValidationError(f"risk_tiers missing keys: {sorted(missing)}")
    risk = data.get("risk") or {}
    # Validate domains
    dom_risk = risk.get("domains") or {}
    unknown_domains = set(dom_risk.keys()) - set(taxonomy.domains)
    if unknown_domains:
        raise TaxonomyValidationError(f"risk_tiers references unknown domains: {sorted(unknown_domains)}")
    # Validate behaviors
    beh_risk = risk.get("behaviors") or {}
    unknown_behaviors = set(beh_risk.keys()) - set(taxonomy.behaviors)
    if unknown_behaviors:
        raise TaxonomyValidationError(f"risk_tiers references unknown behaviors: {sorted(unknown_behaviors)}")
    # Validate axis bins
    axes_risk = risk.get("axes") or {}
    for axis_name, mapping in axes_risk.items():
        if axis_name not in taxonomy.axes:
            raise TaxonomyValidationError(f"risk_tiers references unknown axis: {axis_name}")
        bins = taxonomy.axes[axis_name]
        unknown_bins = set(mapping.keys()) - set(bins)
        if unknown_bins:
            raise TaxonomyValidationError(
                f"risk_tiers axis '{axis_name}' references unknown bins: {sorted(unknown_bins)}"
            )
        # Validate risk labels
        for b, label in mapping.items():
            if label not in ("high", "medium", "low", "excluded"):
                raise TaxonomyValidationError(
                    f"risk_tiers axis '{axis_name}' bin '{b}' has invalid label '{label}'"
                )
    # Validate strategy allocation
    strat = data.get("strategy") or {}
    alloc = strat.get("allocation") or {}
    for key in ("per_behavior_total", "high", "medium", "low", "min_per_domain"):
        if key not in alloc:
            raise TaxonomyValidationError(f"allocation missing '{key}'")
        if not isinstance(alloc[key], (int, float)):
            raise TaxonomyValidationError(f"allocation '{key}' must be number")
    total = alloc["high"] + alloc["medium"] + alloc["low"]
    if int(total) != int(alloc["per_behavior_total"]):
        raise TaxonomyValidationError(
            f"allocation mismatch: high+medium+low={total} != per_behavior_total={alloc['per_behavior_total']}"
        )
    return RiskTiers(version=str(data["version"]), strategy=strat, risk=risk)


def load_commerce_config(
    taxonomy_path: str | Path = Path("configs/commerce_taxonomy.json"),
    risk_tiers_path: str | Path = Path("configs/risk_tiers.json"),
) -> Dict[str, Any]:
    """Load and validate Commerce taxonomy and risk tiers into a single config dict."""
    tax = load_taxonomy(taxonomy_path)
    risk = load_risk_tiers(risk_tiers_path, tax)
    return {
        "taxonomy": tax.__dict__,
        "risk_tiers": risk.__dict__,
    }
