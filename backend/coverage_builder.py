from __future__ import annotations

import re
from typing import Dict, Any, Iterable, List, Optional, Tuple

from .coverage_engine import CoverageEngine, Scenario
from .conversation_generator import conversation_from_scenario


def _slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


def _new_dataset(dataset_id: str, version: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
    return {
        "dataset_id": dataset_id,
        "version": version,
        "metadata": {
            # Keep schema-compatible domain label; use 'commerce' as base tag
            "domain": "commerce",
            "difficulty": "mixed",
            "tags": tags or [],
        },
        "conversations": [],
    }


def _new_golden(dataset_id: str, version: str) -> Dict[str, Any]:
    return {
        "dataset_id": dataset_id,
        "version": version,
        "entries": [],
    }


def _append_scenario(
    ds: Dict[str, Any],
    gd: Dict[str, Any],
    sc: Scenario,
    seen_ids: set,
) -> None:
    if sc.id in seen_ids:
        return
    conv, golden_entry = conversation_from_scenario(sc)
    ds["conversations"].append(conv)
    gd["entries"].append(golden_entry)
    seen_ids.add(sc.id)


def build_per_behavior_datasets(
    eng: Optional[CoverageEngine] = None,
    *,
    domains: Optional[Iterable[str]] = None,
    behaviors: Optional[Iterable[str]] = None,
    version: str = "1.0.0",
) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    eng = eng or CoverageEngine()
    tax = eng.taxonomy
    all_domains = list(domains) if domains is not None else list(tax.get("domains", []))
    all_behaviors = list(behaviors) if behaviors is not None else list(tax.get("behaviors", []))

    outputs: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
    for d in all_domains:
        for b in all_behaviors:
            ds_id = f"coverage-{_slugify(d)}-{_slugify(b)}-{version}"
            ds = _new_dataset(ds_id, version, tags=["per-behavior", _slugify(d), _slugify(b)])
            gd = _new_golden(ds_id, version)
            seen: set = set()
            for sc in eng.scenarios_for(d, b):
                _append_scenario(ds, gd, sc, seen)
            outputs.append((ds, gd))
    return outputs


def build_domain_combined_datasets(
    eng: Optional[CoverageEngine] = None,
    *,
    domains: Optional[Iterable[str]] = None,
    behaviors: Optional[Iterable[str]] = None,
    version: str = "1.0.0",
) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    eng = eng or CoverageEngine()
    tax = eng.taxonomy
    all_domains = list(domains) if domains is not None else list(tax.get("domains", []))
    all_behaviors = list(behaviors) if behaviors is not None else list(tax.get("behaviors", []))

    outputs: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
    for d in all_domains:
        ds_id = f"coverage-{_slugify(d)}-combined-{version}"
        ds = _new_dataset(ds_id, version, tags=["combined", _slugify(d)])
        gd = _new_golden(ds_id, version)
        seen: set = set()
        for b in all_behaviors:
            for sc in eng.scenarios_for(d, b):
                _append_scenario(ds, gd, sc, seen)
        outputs.append((ds, gd))
    return outputs


def build_global_combined_dataset(
    eng: Optional[CoverageEngine] = None,
    *,
    domains: Optional[Iterable[str]] = None,
    behaviors: Optional[Iterable[str]] = None,
    version: str = "1.0.0",
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    eng = eng or CoverageEngine()
    tax = eng.taxonomy
    all_domains = list(domains) if domains is not None else list(tax.get("domains", []))
    all_behaviors = list(behaviors) if behaviors is not None else list(tax.get("behaviors", []))

    ds_id = f"coverage-global-combined-{version}"
    ds = _new_dataset(ds_id, version, tags=["combined", "global"])
    gd = _new_golden(ds_id, version)
    seen: set = set()
    for d in all_domains:
        for b in all_behaviors:
            for sc in eng.scenarios_for(d, b):
                _append_scenario(ds, gd, sc, seen)
    return ds, gd
