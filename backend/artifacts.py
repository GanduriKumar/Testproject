from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import json
import csv
import re
import hashlib


def safe_component(name: str, *, max_len: int = 120) -> str:
    """Return a filesystem-safe folder/file component.
    - Replace disallowed characters with '_'
    - Collapse consecutive underscores
    - Trim to max_len and append short hash for uniqueness
    """
    # Allow only alnum, dash, underscore, dot
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    cleaned = re.sub(r"_+", "_", cleaned).strip("._")
    if not cleaned:
        cleaned = "id"
    h = hashlib.sha1(name.encode("utf-8")).hexdigest()[:8]
    # Ensure length and uniqueness suffix
    base = cleaned[: max(1, max_len - 9)]  # leave room for '-' + 8
    safe = f"{base}-{h}"
    return safe


def conversation_dirname(conversation_id: str) -> str:
    """Produce a very short, stable folder name for a conversation ID.
    This avoids Windows MAX_PATH issues by not embedding long IDs in paths.
    """
    h = hashlib.sha1(conversation_id.encode("utf-8")).hexdigest()[:12]
    return f"c-{h}"


@dataclass
class RunFolderLayout:
    runs_root: Path

    def run_dir(self, run_id: str) -> Path:
        p = self.runs_root / run_id
        p.mkdir(parents=True, exist_ok=True)
        return p

    def conversations_dir(self, run_id: str) -> Path:
        p = self.run_dir(run_id) / "conversations"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def conversation_subdir(self, run_id: str, conversation_id: str) -> Path:
        # Use short hashed folder names to keep paths well under MAX_PATH
        return self.conversations_dir(run_id) / conversation_dirname(conversation_id)

    def run_config_path(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "run_config.json"

    def results_json_path(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "results.json"

    def results_csv_path(self, run_id: str) -> Path:
        return self.run_dir(run_id) / "results.csv"


class RunArtifactWriter:
    def __init__(self, runs_root: Path) -> None:
        self.layout = RunFolderLayout(runs_root=runs_root)

    def init_run(self, run_id: str, config: Dict[str, Any]) -> Path:
        path = self.layout.run_config_path(run_id)
        path.write_text(json.dumps(config, indent=2), encoding="utf-8")
        # ensure conversations dir exists for turn artifacts
        self.layout.conversations_dir(run_id)
        return path

    def write_results_json(self, run_id: str, results: Dict[str, Any]) -> Path:
        path = self.layout.results_json_path(run_id)
        path.write_text(json.dumps(results, indent=2), encoding="utf-8")
        return path

    def write_results_csv(self, run_id: str, results: Dict[str, Any]) -> Path:
        """
        Expect results structure:
        {
          "run_id": str,
          "dataset_id": str,
          "model_spec": str,
          "conversations": [
            { "conversation_id": str,
              "summary": { "conversation_pass": bool, "weighted_pass_rate": float },
              "turns": [
                 { "turn_index": int, "metrics": { "exact": {...}, "semantic": {...}, "adherence": {...}, "hallucination": {...}, "consistency": {...} } }
              ]
            }
          ]
        }
        """
        path = self.layout.results_csv_path(run_id)
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            header = [
                "run_id", "dataset_id", "model_spec",
                "conversation_id", "conversation_pass", "weighted_pass_rate",
                "turn_index",
                "exact_pass", "semantic_pass", "semantic_score_max",
                "adherence_pass", "hallucination_pass", "consistency_pass",
            ]
            writer.writerow(header)
            run_id_val = results.get("run_id")
            dataset_id = results.get("dataset_id")
            model_spec = results.get("model_spec")
            for conv in results.get("conversations", []) or []:
                cid = conv.get("conversation_id")
                summ = conv.get("summary", {})
                cpass = summ.get("conversation_pass")
                wr = summ.get("weighted_pass_rate")
                for t in conv.get("turns", []) or []:
                    idx = t.get("turn_index")
                    mets = t.get("metrics", {})
                    ex = mets.get("exact") or {}
                    se = mets.get("semantic") or {}
                    ad = mets.get("adherence") or {}
                    ha = mets.get("hallucination") or {}
                    co = mets.get("consistency") or {}
                    row = [
                        run_id_val, dataset_id, model_spec,
                        cid, cpass, wr,
                        idx,
                        bool(ex.get("pass")), bool(se.get("pass")), se.get("score_max"),
                        bool(ad.get("pass")), bool(ha.get("pass")), bool(co.get("pass")),
                    ]
                    writer.writerow(row)
        return path


class RunArtifactReader:
    def __init__(self, runs_root: Path) -> None:
        self.layout = RunFolderLayout(runs_root=runs_root)

    def read_results_json(self, run_id: str) -> Dict[str, Any]:
        path = self.layout.results_json_path(run_id)
        data = json.loads(path.read_text(encoding="utf-8"))
        return data
