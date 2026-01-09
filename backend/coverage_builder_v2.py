from __future__ import annotations
from typing import Any, Dict, List, Tuple, Optional, Iterable

from .risk_sampler import sample_for_behavior
from .convgen_v2 import build_records
from .commerce_taxonomy import load_commerce_config


def build_per_behavior_datasets_v2(
    *,
    domains: Optional[Iterable[str]] = None,
    behaviors: Optional[Iterable[str]] = None,
    version: str = "1.0.0",
    seed: int = 42,
) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    cfg = load_commerce_config()
    tax = cfg["taxonomy"]
    all_domains = list(domains) if domains is not None else list(tax.get("domains", []))
    all_behaviors = list(behaviors) if behaviors is not None else list(tax.get("behaviors", []))

    outputs: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
    for b in all_behaviors:
        manifest = sample_for_behavior(cfg, b)
        # Filter by domain if provided
        for sc in manifest.get("scenarios", []):
            d = sc.get("domain")
            if domains is not None and d not in all_domains:
                continue
            axes = sc.get("axes", {})
            ds, gd = build_records(domain=d, behavior=b, axes=axes, version=version, seed=seed)
            outputs.append((ds, gd))
    return outputs


def build_domain_combined_datasets_v2(
    *,
    domains: Optional[Iterable[str]] = None,
    behaviors: Optional[Iterable[str]] = None,
    version: str = "1.0.0",
    seed: int = 42,
) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    # Group per domain: aggregate conversations and goldens
    per = build_per_behavior_datasets_v2(domains=domains, behaviors=behaviors, version=version, seed=seed)
    by_domain: Dict[str, Tuple[Dict[str, Any], Dict[str, Any]]] = {}
    for ds, gd in per:
        # each ds currently has one conversation; append into domain bucket
        meta = ds.get("conversations", [{}])[0].get("metadata", {})
        domain_label = meta.get("domain_label") or (ds.get("dataset_id", "").split("-")[0])
        key = domain_label
        if key not in by_domain:
            by_domain[key] = ({
                "dataset_id": f"coverage-{key.replace(' ', '-').lower()}-combined-{version}",
                "version": version,
                "metadata": {"domain": "commerce", "difficulty": "mixed", "tags": ["combined", key]},
                "conversations": [],
            }, {"dataset_id": f"coverage-{key.replace(' ', '-').lower()}-combined-{version}", "version": version, "entries": []})
        by_domain[key][0]["conversations"].extend(ds.get("conversations", []))
        by_domain[key][1]["entries"].extend(gd.get("entries", []))
    return list(by_domain.values())


def build_global_combined_dataset_v2(
    *,
    domains: Optional[Iterable[str]] = None,
    behaviors: Optional[Iterable[str]] = None,
    version: str = "1.0.0",
    seed: int = 42,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    per = build_per_behavior_datasets_v2(domains=domains, behaviors=behaviors, version=version, seed=seed)
    ds = {
        "dataset_id": f"coverage-global-combined-{version}",
        "version": version,
        "metadata": {"domain": "commerce", "difficulty": "mixed", "tags": ["combined", "global"]},
        "conversations": [],
    }
    gd = {"dataset_id": ds["dataset_id"], "version": version, "entries": []}
    for d, g in per:
        ds["conversations"].extend(d.get("conversations", []))
        gd["entries"].extend(g.get("entries", []))
    return ds, gd
