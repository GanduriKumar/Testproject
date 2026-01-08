from backend.coverage_manifest import CoverageManifestor


def test_manifest_structure_and_pair_lookup():
    cm = CoverageManifestor()
    manifest = cm.build(seed=123)
    assert "pairs" in manifest and isinstance(manifest["pairs"], list)
    assert manifest["axes_order"] == [
        "price_sensitivity",
        "brand_bias",
        "availability",
        "policy_boundary",
    ]

    # pick one domain/behavior from taxonomy and verify
    p = cm.get_pair(manifest, "Returns, Refunds & Exchanges", "Happy Path")
    assert p is not None
    assert "raw_total" in p and p["raw_total"] == 108
    assert "final_total" in p and p["final_total"] <= 108
    assert isinstance(p["breakdown"], list)
    assert isinstance(p["scenarios"], list)
    # scenarios carry ids and axes
    if p["scenarios"]:
        s0 = p["scenarios"][0]
        assert "id" in s0 and "axes" in s0


def test_manifest_deterministic_with_seed():
    cm = CoverageManifestor()
    m1 = cm.build(seed=7)
    m2 = cm.build(seed=7)
    # same seed -> identical manifests
    assert m1 == m2
