from backend.coverage_engine import CoverageEngine
from backend.conversation_generator import conversation_from_scenario
from backend.schemas import SchemaValidator


def test_generated_conversation_and_golden_schema_compliance():
    eng = CoverageEngine()
    tax = eng.taxonomy
    # Pick a deterministic scenario: first from Returns domain, Happy Path
    scenarios = eng.scenarios_for("Returns, Refunds & Exchanges", "Happy Path")
    assert scenarios, "No scenarios generated"
    sc = scenarios[0]

    dataset_conv, golden_entry = conversation_from_scenario(sc)

    # Wrap into dataset and golden documents
    dataset_doc = {
        "dataset_id": "gen-returns-happy",
        "version": "1.0.0",
        "metadata": {
            "domain": "commerce",
            "difficulty": "mixed"
        },
        "conversations": [dataset_conv]
    }

    golden_doc = {
        "dataset_id": "gen-returns-happy",
        "version": "1.0.0",
        "entries": [golden_entry]
    }

    sv = SchemaValidator()
    assert sv.validate("dataset", dataset_doc) == []
    assert sv.validate("golden", golden_doc) == []

    # Outcome alignment: if out-of-policy then DENY
    axes = dict(sc.axes)
    if axes["policy_boundary"] == "out-of-policy":
        assert golden_entry["final_outcome"]["decision"] == "DENY"
