from __future__ import annotations
from typing import Any, Dict, List, Optional


def _eq_optional(expected: Optional[Any], actual: Optional[Any]) -> bool:
    if expected is None:
        return True
    return expected == actual


def check_final_outcome(final_state: Dict[str, Any], expected_outcome: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare expected final outcome fields (if provided) against the extracted final_state.
    Fields: decision (required in expected), refund_amount?, reason_code?, next_action?, policy_flags?
    policy_flags check is subset: all expected flags must appear in state.policy_flags
    """
    reasons: List[str] = []
    exp_decision = expected_outcome.get("decision")
    if exp_decision is None:
        reasons.append("expected decision missing")
    act_decision = final_state.get("decision")
    if exp_decision is not None and act_decision != exp_decision:
        reasons.append(f"decision mismatch: expected={exp_decision}, actual={act_decision}")

    for key in ("refund_amount", "reason_code", "next_action"):
        if key in expected_outcome and not _eq_optional(expected_outcome.get(key), final_state.get(key)):
            reasons.append(f"{key} mismatch: expected={expected_outcome.get(key)}, actual={final_state.get(key)}")

    if "policy_flags" in expected_outcome:
        exp_flags = set(expected_outcome.get("policy_flags") or [])
        act_flags = set(final_state.get("policy_flags") or [])
        missing = [f for f in exp_flags if f not in act_flags]
        if missing:
            reasons.append(f"missing policy_flags: {missing}")

    passed = len(reasons) == 0
    return {"metric": "final_outcome", "pass": passed, "reasons": reasons}


def aggregate_conversation(
    per_turn_results: List[Dict[str, Any]],
    final_state: Dict[str, Any],
    expected_outcome: Dict[str, Any],
    weights: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """
    Outcome-first rule: conversation passes only if final outcome passes and
    no high-severity violations on the final turn (adherence/hallucination failures).

    per_turn_results: list of {turn_index, metrics: {name: {pass: bool, ...}, ...}}
    """
    outcome = check_final_outcome(final_state, expected_outcome)

    # Determine high-severity violations on final assistant turn if present
    last = per_turn_results[-1] if per_turn_results else {"metrics": {}}
    last_metrics = last.get("metrics", {})
    severe_fail = False
    sev_reasons: List[str] = []
    for m in ("adherence", "hallucination"):
        mres = last_metrics.get(m)
        if isinstance(mres, dict) and mres.get("pass") is False:
            severe_fail = True
            sev_reasons.append(f"{m} failed on final turn")

    # Aggregate a simple weighted pass rate across turns using per-turn rollup if present,
    # else fallback to (exact.pass or semantic.pass)
    n = len(per_turn_results)
    if n == 0:
        weighted_score = 0.0
        passed_turns = 0
    else:
        w = weights or [1.0] * n
        # normalize
        total_w = sum(w) if sum(w) > 0 else 1.0
        total = 0.0
        passed_turns = 0
        for i, r in enumerate(per_turn_results):
            if "turn_pass" in r:
                turn_pass = bool(r.get("turn_pass"))
            else:
                mets = r.get("metrics", {})
                turn_pass = False
                ex = mets.get("exact")
                se = mets.get("semantic")
                if isinstance(ex, dict) and ex.get("pass"):
                    turn_pass = True
                if isinstance(se, dict) and se.get("pass"):
                    turn_pass = True
            if turn_pass:
                passed_turns += 1
                total += w[i]
        weighted_score = total / total_w

    convo_pass = bool(outcome.get("pass")) and not severe_fail

    return {
        "conversation_pass": convo_pass,
        "final_outcome": outcome,
        "high_severity_violation": severe_fail,
        "severity_reasons": sev_reasons,
        "turns_total": n,
        "turns_passed": passed_turns,
        "weighted_pass_rate": weighted_score,
    }
