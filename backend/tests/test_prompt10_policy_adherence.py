from __future__ import annotations

from backend.metrics_extra import adherence


def test_adherence_allows_refund_within_limits():
    out = "Approved. We'll issue a refund of $10 to your original payment method."
    constraints = {"refund_after_ship": False, "max_refund": 20}
    res = adherence(out, constraints, expected_decision="ALLOW")
    assert res["pass"] is True
    assert not res.get("flags")


def test_adherence_exceeds_max_refund_flag():
    out = "We'll refund $50 for this order."
    constraints = {"max_refund": 10}
    res = adherence(out, constraints, expected_decision="ALLOW")
    assert res["pass"] is False
    assert "exceeds_max_refund" in (res.get("flags") or [])


def test_incorrect_refusal_detected_for_allowed():
    out = "Unfortunately we cannot process a refund for this case."
    constraints = {"max_refund": 10}
    res = adherence(out, constraints, expected_decision="ALLOW")
    assert res["pass"] is False
    assert "incorrect_refusal" in (res.get("flags") or [])


def test_refund_after_ship_violation():
    out = "We can refund it after it's shipped."
    constraints = {"refund_after_ship": False}
    res = adherence(out, constraints, expected_decision="ALLOW")
    assert res["pass"] is False
    assert any("refund_after_ship" in r for r in res.get("reasons") or [])
