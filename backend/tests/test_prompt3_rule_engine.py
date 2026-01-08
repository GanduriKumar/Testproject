from backend.coverage_engine import CoverageEngine, enumerate_scenarios, AXES_ORDER


def test_enumeration_cartesian_counts():
    eng = CoverageEngine()
    tax = eng.taxonomy
    # 3 x 3 x 4 x 3 = 108 per domain/behavior
    sc = enumerate_scenarios(tax, "Returns, Refunds & Exchanges", "Ambiguous Queries")
    assert len(sc) == 108
    # sanity: axes present in fixed order
    a0 = sc[0]
    assert tuple(k for k, _ in a0.axes) == tuple(AXES_ORDER)


def test_rule_application_physical_impossibility():
    eng = CoverageEngine()
    scenarios = eng.scenarios_for("Shipping & Delivery", "Constraint-heavy Queries")
    # physical impossibility excludes availability backorder/out-of-stock for same-day pickup implication
    # raw 108 - (for the two availability bins across all 3*3*3 other combos = 54) = 54
    # Note: other rules might further adjust in config (none do specifically for this domain/behavior combination except this rule)
    assert len(scenarios) <= 108
    # ensure no scenario has availability backorder or out-of-stock
    for sc in scenarios:
        availability = dict(sc.axes)["availability"]
        assert availability not in {"backorder", "out-of-stock"}


def test_rule_application_business_irrelevance_brand_bias_removed():
    eng = CoverageEngine()
    scenarios = eng.scenarios_for("System Awareness & Failure Handling", "Happy Path")
    for sc in scenarios:
        brand = dict(sc.axes)["brand_bias"]
        assert brand == "none"


def test_low_risk_cap_applied_within_policy_instock():
    eng = CoverageEngine()
    scenarios = eng.scenarios_for("Product Discovery & Search", "Happy Path")
    # Count subset matching in-stock within-policy, ensure capped at 12
    subset = [
        sc for sc in scenarios
        if dict(sc.axes)["availability"] == "in-stock" and dict(sc.axes)["policy_boundary"] == "within-policy"
    ]
    assert len(subset) <= 12


def test_regulatory_block_out_of_policy_removed_in_happy_path():
    eng = CoverageEngine()
    scenarios = eng.scenarios_for("Cart Management", "Happy Path")
    for sc in scenarios:
        assert dict(sc.axes)["policy_boundary"] != "out-of-policy"


def test_skew_control_extreme_combo_capped():
    eng = CoverageEngine()
    scenarios = eng.scenarios_for("Checkout & Payments", "Adversarial/Trap Queries")
    extreme = [
        sc for sc in scenarios
        if (
            dict(sc.axes)["price_sensitivity"] == "high"
            and dict(sc.axes)["policy_boundary"] == "out-of-policy"
            and dict(sc.axes)["availability"] == "out-of-stock"
            and dict(sc.axes)["brand_bias"] == "hard"
        )
    ]
    assert len(extreme) <= 1
