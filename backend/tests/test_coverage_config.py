from pathlib import Path

from backend.coverage_config import CoverageConfig


def test_load_taxonomy_and_exclusions():
    cfg = CoverageConfig()
    tax = cfg.load_taxonomy()
    exc = cfg.load_exclusions()

    # basic shape
    assert isinstance(tax["domains"], list) and len(tax["domains"]) >= 1
    assert isinstance(tax["behaviors"], list) and len(tax["behaviors"]) >= 1
    axes = tax["axes"]
    for k in ("price_sensitivity", "brand_bias", "availability", "policy_boundary"):
        assert isinstance(axes[k], list) and len(axes[k]) >= 1

    assert isinstance(exc["rules"], list) and len(exc["rules"]) >= 1


def test_governance_lints(tmp_path: Path):
    cfg = CoverageConfig(root=tmp_path / "configs")
    (tmp_path / "configs").mkdir(parents=True, exist_ok=True)

    # Write minimal taxonomy with duplicates to trigger lint
    (tmp_path / "configs" / "taxonomy.json").write_text(
        '{"domains":["A","A"],"behaviors":["B"],"axes":{"price_sensitivity":["low"],"brand_bias":["none"],"availability":["in"],"policy_boundary":["within"]}}',
        encoding="utf-8",
    )
    (tmp_path / "configs" / "exclusions.json").write_text(
        '{"rules":[]}', encoding="utf-8"
    )
    try:
        cfg.load_taxonomy()
        assert False, "expected duplicate lint to raise"
    except ValueError as e:
        assert "Duplicate" in str(e)

    # Now write valid taxonomy and conflicting exclusions
    (tmp_path / "configs" / "taxonomy.json").write_text(
        '{"domains":["A"],"behaviors":["B"],"axes":{"price_sensitivity":["low"],"brand_bias":["none"],"availability":["in"],"policy_boundary":["within"]}}',
        encoding="utf-8",
    )
    (tmp_path / "configs" / "exclusions.json").write_text(
        '{"rules":[{"name":"r1","type":"low_risk_cap","applies":{},"when":{},"cap":2},{"name":"r2","type":"low_risk_cap","applies":{},"when":{},"cap":1}]}',
        encoding="utf-8",
    )
    try:
        cfg.load_exclusions()
        assert False, "expected conflicting rules lint to raise"
    except ValueError as e:
        assert "Multiple caps" in str(e)
