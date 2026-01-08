import pytest

from backend.schemas import SchemaValidator


def test_dataset_difficulty_mixed_valid():
    validator = SchemaValidator()
    data = {
        "dataset_id": "demo-combined",
        "version": "1.0.0",
        "metadata": {
            "domain": "commerce",
            "difficulty": "mixed",
            "tags": ["combined", "coverage"]
        },
        "conversations": [
            {
                "conversation_id": "conv1",
                "turns": [
                    {"role": "user", "text": "I want a refund"},
                    {"role": "assistant", "text": "Sure, let's check your order"}
                ]
            }
        ]
    }
    errors = validator.validate("dataset", data)
    assert errors == []


def test_dataset_difficulty_array_valid():
    validator = SchemaValidator()
    data = {
        "dataset_id": "demo-multi-diff",
        "version": "1.0.0",
        "metadata": {
            "domain": "commerce",
            "difficulty": ["easy", "hard"],
            "tags": ["combined", "coverage"]
        },
        "conversations": [
            {
                "conversation_id": "convA",
                "turns": [
                    {"role": "user", "text": "Where is my order?"},
                    {"role": "assistant", "text": "Tracking shows it's out for delivery."}
                ]
            }
        ]
    }
    errors = validator.validate("dataset", data)
    assert errors == []


def test_dataset_difficulty_array_invalid_values():
    validator = SchemaValidator()
    data = {
        "dataset_id": "demo-invalid",
        "version": "1.0.0",
        "metadata": {
            "domain": "commerce",
            "difficulty": ["easy", "mixed"],  # 'mixed' not allowed inside array
        },
        "conversations": [
            {
                "conversation_id": "convB",
                "turns": [
                    {"role": "user", "text": "Help"},
                    {"role": "assistant", "text": "Ok"}
                ]
            }
        ]
    }
    errors = validator.validate("dataset", data)
    assert any("difficulty" in e for e in errors)


def test_golden_with_constraints_and_policy_flags_valid():
    validator = SchemaValidator()
    golden = {
        "dataset_id": "demo-combined",
        "version": "1.0.0",
        "entries": [
            {
                "conversation_id": "conv1",
                "turns": [
                    {
                        "turn_index": 0,
                        "expected": {"variants": ["Ask for order number"]}
                    }
                ],
                "final_outcome": {
                    "decision": "ALLOW",
                    "refund_amount": 10.0,
                    "policy_flags": ["NEEDS_EVIDENCE"]
                },
                "constraints": {
                    "refund_after_ship": False
                }
            }
        ]
    }
    errors = validator.validate("golden", golden)
    assert errors == []
