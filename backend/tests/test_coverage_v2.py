from __future__ import annotations
import json
from pathlib import Path

from backend.coverage_builder_v2 import (
    build_per_behavior_datasets_v2,
    build_domain_combined_datasets_v2,
    build_global_combined_dataset_v2,
)
from backend.schemas import SchemaValidator


def test_per_behavior_deterministic(tmp_path: Path):
    out1 = build_per_behavior_datasets_v2(version="9.9.9", seed=123)
    out2 = build_per_behavior_datasets_v2(version="9.9.9", seed=123)
    # Compare dataset_ids and counts
    ids1 = [d[0]["dataset_id"] for d in out1]
    ids2 = [d[0]["dataset_id"] for d in out2]
    assert ids1 == ids2
    assert sum(len(d[0]["conversations"]) for d in out1) == sum(len(d[0]["conversations"]) for d in out2)


def test_schemas_valid(tmp_path: Path):
    sv = SchemaValidator()
    per = build_per_behavior_datasets_v2(version="9.9.9")
    for ds, gd in per:
        assert sv.validate("dataset", ds) == []
        assert sv.validate("golden", gd) == []

    dom = build_domain_combined_datasets_v2(version="9.9.9")
    for ds, gd in dom:
        assert sv.validate("dataset", ds) == []
        assert sv.validate("golden", gd) == []

    ds, gd = build_global_combined_dataset_v2(version="9.9.9")
    assert sv.validate("dataset", ds) == []
    assert sv.validate("golden", gd) == []


def test_cli_coverage_v2_writes(tmp_path: Path, monkeypatch):
    # Write outputs to a temp datasets dir
    out_dir = tmp_path / "datasets"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Generate domain combined + global
    dom = build_domain_combined_datasets_v2(version="9.9.9")
    dom.append(build_global_combined_dataset_v2(version="9.9.9"))

    # Save and verify
    for ds, gd in dom:
        ds_path = out_dir / f"{ds['dataset_id']}.dataset.json"
        gd_path = out_dir / f"{ds['dataset_id']}.golden.json"
        ds_path.parent.mkdir(parents=True, exist_ok=True)
        ds_path.write_text(json.dumps(ds), encoding="utf-8")
        gd_path.write_text(json.dumps(gd), encoding="utf-8")
        assert ds_path.exists()
        assert gd_path.exists()
