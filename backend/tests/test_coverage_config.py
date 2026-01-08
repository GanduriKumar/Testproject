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
