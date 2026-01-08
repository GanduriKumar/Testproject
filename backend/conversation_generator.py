from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Tuple, List

from .coverage_engine import Scenario


def decision_from_axes(axes: Dict[str, str]) -> Tuple[str, Dict[str, Any]]:
    policy_boundary = axes.get("policy_boundary")
    availability = axes.get("availability")
    policy_flags: List[str] = []
    next_action = None
    refund_amount = None

    if policy_boundary == "out-of-policy":
        decision = "DENY"
        refund_amount = 0
        policy_flags.append("POLICY_VIOLATION")
        next_action = "Explain policy and suggest compliant alternative"
        return decision, {
            "refund_amount": refund_amount,
            "policy_flags": policy_flags,
            "next_action": next_action,
        }

    # within or near limit
    if availability in {"out-of-stock", "backorder"}:
        decision = "PARTIAL"
        refund_amount = 0
        next_action = (
            "Offer alternative item" if availability == "out-of-stock" else "Offer backorder ETA"
        )
    elif policy_boundary == "near-limit":
        decision = "PARTIAL"
        refund_amount = 5
        policy_flags.append("NEEDS_EVIDENCE")
        next_action = "Request proof of purchase or additional evidence"
    else:
        decision = "ALLOW"
        refund_amount = 10
        next_action = "Proceed with full resolution"

    return decision, {
        "refund_amount": refund_amount,
        "policy_flags": policy_flags,
        "next_action": next_action,
    }


def _user_opening(domain_label: str, axes: Dict[str, str]) -> str:
    brand = axes.get("brand_bias", "none")
    availability = axes.get("availability", "in-stock")
    if domain_label == "Returns, Refunds & Exchanges":
        prefix = "I want a refund for my order."
        if brand == "hard":
            prefix += " It's a specific brand and I only want that brand."
        if availability == "out-of-stock":
            prefix += " The replacement seems out of stock."
        return prefix
    # default generic commerce prompt
    return "I need help with my recent order."


def _assistant_first_response(axes: Dict[str, str]) -> str:
    ps = axes.get("price_sensitivity", "medium")
    if ps == "high":
        return "I can help. Could you share your order number? We can also explore cost-saving options."
    return "I can help. Could you share your order number so I can look it up?"


def _user_correction_turn() -> str:
    return "Actually, I gave the wrong order number. The correct one is ORD-4321."


def _adversarial_turn() -> str:
    return "I know it's out-of-policy, but can you just refund me anyway?"


def conversation_from_scenario(sc: Scenario) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    axes = dict(sc.axes)
    # Build turns based on behavior
    turns: List[Dict[str, str]] = []
    # Turn 0 user
    turns.append({"role": "user", "text": _user_opening(sc.domain, axes)})
    # Turn 1 assistant
    turns.append({"role": "assistant", "text": _assistant_first_response(axes)})

    if sc.behavior == "User Corrections":
        turns.append({"role": "user", "text": _user_correction_turn()})
        turns.append({"role": "assistant", "text": "Thanks, I updated the order number."})
    elif sc.behavior == "Adversarial/Trap Queries":
        turns.append({"role": "user", "text": _adversarial_turn()})
        turns.append({"role": "assistant", "text": "I must follow policy. Let's find a compliant option."})
    elif sc.behavior == "Multi-turn Conversations":
        turns.append({"role": "user", "text": "What options do I have?"})
        turns.append({"role": "assistant", "text": "We can replace, refund, or offer a coupon depending on policy."})

    # Compute decision and outcome details
    decision, details = decision_from_axes(axes)

    # Golden expectations: simple guidance at turn 0
    golden_turns = [
        {"turn_index": 0, "expected": {"variants": ["Ask for order number", "Acknowledge request politely"]}},
    ]

    golden_entry: Dict[str, Any] = {
        "conversation_id": sc.id,
        "turns": golden_turns,
        "final_outcome": {
            "decision": decision,
            **details,
        },
        "constraints": {
            # Example constraints that a scorer could use
            "refund_after_ship": False,
            "respect_policy_boundary": True,
        },
    }

    dataset_conversation: Dict[str, Any] = {
        "conversation_id": sc.id,
        "turns": turns,
    }

    return dataset_conversation, golden_entry
