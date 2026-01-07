import json
from pathlib import Path
import tempfile

from artifacts import RunArtifactWriter, RunArtifactReader


def sample_results():
    return {
        "run_id": "rid",
        "dataset_id": "ds1",
        "model_spec": "ollama:llama3.2:latest",
        "conversations": [
            {
                "conversation_id": "c1",
                "summary": {"conversation_pass": True, "weighted_pass_rate": 0.9},
                "turns": [
                    {"turn_index": 1, "metrics": {"exact": {"pass": True}}},
                    {"turn_index": 2, "metrics": {"semantic": {"pass": False, "score_max": 0.5}}}
                ]
            }
        ]
    }


def test_write_and_read_json_and_csv():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        w = RunArtifactWriter(root)
        rid = "rid"
        w.init_run(rid, {"dataset_id": "ds1"})
        res = sample_results()
        w.write_results_json(rid, res)
        p = w.write_results_csv(rid, res)
        assert p.exists()
        # smoke read json
        r = RunArtifactReader(root)
        data = r.read_results_json(rid)
        assert data["run_id"] == "rid"
        # check csv rows
        content = p.read_text(encoding="utf-8").splitlines()
        assert len(content) >= 2
