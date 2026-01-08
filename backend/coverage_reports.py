from __future__ import annotations

import csv
from io import StringIO
from typing import Any, Dict, List, Optional, Tuple

from .coverage_manifest import CoverageManifestor, build_manifest
from .schemas import SchemaValidator


def coverage_summary_csv(domains: Optional[List[str]] = None, behaviors: Optional[List[str]] = None, seed: int = 42) -> str:
    cm = CoverageManifestor()
    manifest = cm.build(seed)
    pairs = manifest.get("pairs", [])
    if domains:
        pairs = [p for p in pairs if p.get("domain") in set(domains)]
    if behaviors:
        pairs = [p for p in pairs if p.get("behavior") in set(behaviors)]

    out = StringIO()
    w = csv.writer(out)
    w.writerow(["domain", "behavior", "raw_total", "removed_exclude", "removed_cap", "final_total"])
    for p in pairs:
        removed_excl = sum(b.get("removed_exclude", 0) for b in p.get("breakdown", []))
        removed_cap = sum(b.get("removed_cap", 0) for b in p.get("breakdown", []))
        w.writerow([p.get("domain"), p.get("behavior"), p.get("raw_total", 0), removed_excl, removed_cap, p.get("final_total", 0)])
    return out.getvalue()


def coverage_heatmap_csv(domains: Optional[List[str]] = None, behaviors: Optional[List[str]] = None, seed: int = 42) -> str:
    cm = CoverageManifestor()
    manifest = cm.build(seed)
    all_behaviors: List[str] = behaviors or cm.taxonomy.get("behaviors", [])
    pairs = manifest.get("pairs", [])
    if domains:
        pairs = [p for p in pairs if p.get("domain") in set(domains)]
    if behaviors:
        pairs = [p for p in pairs if p.get("behavior") in set(behaviors)]

    # Build map domain -> behavior -> final_total
    grid: Dict[str, Dict[str, int]] = {}
    for p in pairs:
        d = p.get("domain")
        b = p.get("behavior")
        grid.setdefault(d, {})[b] = int(p.get("final_total", 0))

    out = StringIO()
    w = csv.writer(out)
    w.writerow(["Domain/Behavior", *all_behaviors])
    for d, cols in grid.items():
        w.writerow([d, *[cols.get(b, 0) for b in all_behaviors]])
    return out.getvalue()


def per_turn_csv(dataset: Dict[str, Any], golden: Dict[str, Any]) -> str:
    # Validate
    sv = SchemaValidator()
    ds_err = sv.validate("dataset", dataset)
    gd_err = sv.validate("golden", golden)
    if ds_err or gd_err:
        raise ValueError(f"schema errors: dataset={ds_err} golden={gd_err}")

    # Build maps
    convo_map: Dict[str, Dict[str, Any]] = {c["conversation_id"]: c for c in dataset.get("conversations", [])}
    exp_map: Dict[str, Dict[int, List[str]]] = {}
    outcomes: Dict[str, Dict[str, Any]] = {}
    for e in golden.get("entries", []):
        cid = e.get("conversation_id")
        exp_map[cid] = {t.get("turn_index"): list((t.get("expected") or {}).get("variants") or []) for t in e.get("turns", [])}
        outcomes[cid] = e.get("final_outcome", {})

    out = StringIO()
    w = csv.writer(out)
    w.writerow(["dataset_id", "conversation_id", "turn_index", "role", "text", "expected_variants", "final_decision"])
    dsid = dataset.get("dataset_id")
    for cid, conv in convo_map.items():
        turns = conv.get("turns", [])
        for idx, t in enumerate(turns):
            expected = ";".join(exp_map.get(cid, {}).get(idx, []))
            w.writerow([dsid, cid, idx, t.get("role"), t.get("text"), expected, ""])
        # add a summary final decision row with turn_index = -1
        outcome = outcomes.get(cid, {})
        w.writerow([dsid, cid, -1, "", "", "", outcome.get("decision")])
    return out.getvalue()
