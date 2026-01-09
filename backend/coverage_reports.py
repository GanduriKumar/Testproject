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
    # Minimal header expected by tests, followed by extended identity columns
    w.writerow([
        "dataset_id", "conversation_id", "turn_index",
        # extended identity
        "conversation_slug", "conversation_title",
        "domain", "behavior", "scenario", "persona", "locale", "channel", "complexity", "case_type",
        # descriptions
        "domain_description", "conversation_description",
        # keys and content
        "turn_key", "role", "text", "expected_variants",
        # final outcome (summary row only)
        "final_decision",
    ])
    dsid = dataset.get("dataset_id")
    import re
    def slugify(text: str) -> str:
        t = (text or "").lower()
        t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
        return t[:80]

    domain_description = (dataset.get("metadata") or {}).get("short_description")
    for cid, conv in convo_map.items():
        turns = conv.get("turns", [])
        meta_ds = dataset.get("metadata", {}) or {}
        meta = conv.get("metadata") or {}
        d = meta.get("domain") or meta_ds.get("domain")
        b = meta.get("behavior") or meta_ds.get("behavior")
        s = meta.get("scenario") or meta.get("case")
        persona = meta.get("persona")
        locale = meta.get("locale")
        channel = meta.get("channel")
        complexity = meta.get("complexity") or meta_ds.get("difficulty")
        case_type = meta.get("case_type") or meta.get("type")
        title = conv.get("title") or ((f"{b}: {s}" if b and s else (b or s)) if (b or s) else None) or cid
        conv_description = meta.get("short_description")
        parts = [p for p in [d, b, s, persona, locale] if p]
        slug = slugify("-".join(parts)) if parts else slugify(cid)
        for idx, t in enumerate(turns):
            expected = ";".join(exp_map.get(cid, {}).get(idx, []))
            turn_key = f"{slug}#{idx}"
            w.writerow([
                # identity (minimal first)
                dsid, cid, idx,
                # extended identity
                slug, title,
                d, b, s, persona, locale, channel, complexity, case_type,
                # descriptions
                domain_description, conv_description,
                # keys and content
                turn_key, t.get("role"), t.get("text"), expected,
                # final outcome
                "",
            ])
        # add a summary final decision row with turn_index = -1
        outcome = outcomes.get(cid, {})
        w.writerow([
            dsid, cid, -1,
            slug, title,
            d, b, s, persona, locale, channel, complexity, case_type,
            # descriptions
            domain_description, conv_description,
            f"{slug}#-1", "", "", "",
            outcome.get("decision"),
        ])
    return out.getvalue()
