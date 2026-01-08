from __future__ import annotations
from pathlib import Path
import json
from typing import Any, Dict

from .schemas import SchemaValidator

SCHEMAS_DIR = Path(__file__).resolve().parents[1] / "configs" / "schemas"


class CoverageConfig:
    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root) if root else Path(__file__).resolve().parents[1] / "configs"
        self.sv = SchemaValidator()

    def load_taxonomy(self, path: Path | None = None) -> Dict[str, Any]:
        p = path or (self.root / "taxonomy.json")
        data = json.loads(p.read_text(encoding="utf-8"))
        # validate against coverage_taxonomy.schema.json via SchemaValidator? It loads dataset/golden/run_config today.
        # For now, validate shape with simple checks to avoid altering SchemaValidator internals.
        if not isinstance(data.get("domains"), list) or not data["domains"]:
            raise ValueError("taxonomy.domains must be a non-empty list")
        if not isinstance(data.get("behaviors"), list) or not data["behaviors"]:
            raise ValueError("taxonomy.behaviors must be a non-empty list")
        axes = data.get("axes") or {}
        for key in ("price_sensitivity", "brand_bias", "availability", "policy_boundary"):
            vals = axes.get(key)
            if not isinstance(vals, list) or not vals:
                raise ValueError(f"taxonomy.axes.{key} must be a non-empty list")
        return data

    def load_exclusions(self, path: Path | None = None) -> Dict[str, Any]:
        p = path or (self.root / "exclusions.json")
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data.get("rules"), list):
            raise ValueError("exclusions.rules must be a list")
        return data
