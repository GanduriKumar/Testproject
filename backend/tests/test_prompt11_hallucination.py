from __future__ import annotations

from backend.metrics_extra import hallucination


def test_hallucination_support_score_pass():
    state = {"order_id": "A1", "refund_amount": 10}
    history = ["User: order A1", "Assistant: will refund $10 on 2025-12-01"]
    out = "Refund of $10 for order A1 will be processed on 2025-12-01."
    res = hallucination(out, state, history, threshold=0.75)
    assert res["pass"] is True
    assert res.get("score", 0) >= 0.75


def test_hallucination_support_score_fail():
    state = {"order_id": "A1"}
    history = ["User: order A1"]
    out = "We will refund $99 on 01/02/2026 for order A2, with a 25% discount."
    res = hallucination(out, state, history, threshold=0.75)
    assert res["pass"] is False
    # Should note unseen entities
    assert any("unseen" in r for r in res.get("reasons", []))


def test_hallucination_backward_compat_no_threshold():
    state = {"order_id": "A1"}
    history = ["User: order A1"]
    out = "Order A1 processed"
    res = hallucination(out, state, history)
    assert res["pass"] is True
