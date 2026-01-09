from __future__ import annotations
from pathlib import Path
import os
from typing import Dict, Any, List
import json
from datetime import datetime, timezone

try:
    from .providers.registry import ProviderRegistry  # type: ignore
    from .providers.types import ProviderRequest  # type: ignore
    from .state_extractor import extract_state  # type: ignore
    from .context_builder import build_context  # type: ignore
except Exception:
    from providers.registry import ProviderRegistry  # type: ignore
    from providers.types import ProviderRequest  # type: ignore
    from state_extractor import extract_state  # type: ignore
    from context_builder import build_context  # type: ignore


class TurnRunner:
    def __init__(self, run_root: Path) -> None:
        self.run_root = Path(run_root)
        self.providers = ProviderRegistry()

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _artifact_path(self, run_id: str, conversation_id: str, turn_index: int) -> Path:
        # Primary (short) layout: <runs_root>/<run_id>/conversations/<conversation_id>/
        base_plain = self.run_root / run_id / "conversations" / conversation_id
        candidate = base_plain / f"turn_{turn_index:03d}.json"
        # Optional override: force hashed conversation folder via env flag
        force_hashed = str(os.getenv("EVAL_FORCE_HASHED_CONV", "")).lower() in ("1", "true", "yes")
        # On Windows, avoid MAX_PATH (260) errors by falling back to hashed conversation folder if too long
        try:
            is_windows = os.name == "nt"
        except Exception:
            is_windows = False
        if force_hashed or (is_windows and len(str(candidate)) >= 240):
            # Use hashed short folder via RunFolderLayout to keep paths short
            try:
                from .artifacts import RunFolderLayout  # type: ignore
            except Exception:
                from artifacts import RunFolderLayout  # type: ignore
            layout = RunFolderLayout(self.run_root)
            base_hashed = layout.conversation_subdir(run_id, conversation_id)
            base_hashed.mkdir(parents=True, exist_ok=True)
            return base_hashed / f"turn_{turn_index:03d}.json"
        # Default plain path
        base_plain.mkdir(parents=True, exist_ok=True)
        return candidate

    async def run_turn(
        self,
        *,
        run_id: str,
        provider: str,
        model: str,
        domain: str,
        conversation_id: str,
        turn_index: int,
        turns: List[Dict[str, str]],
        conv_meta: Dict[str, Any] | None = None,
        params_override: Dict[str, Any] | None = None,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        started_at = self._now_iso()
        # 1) derive state from transcript
        state = extract_state(domain, turns)
        # 2) build provider-ready context
        # Build context with conversation-level metadata (policy + facts) when available
        ctx = build_context(domain, turns, state, max_tokens=max_tokens, conv_meta=conv_meta or {}, params_override=params_override)
        messages = ctx["messages"]
        params = ctx.get("params") or {}
        # 3) call provider
        adapter = self.providers.get(provider)
        req = ProviderRequest(model=model, messages=messages, metadata={
            "run_id": run_id,
            "conversation_id": conversation_id,
            "turn_index": turn_index,
            "domain": domain,
            "params": params,
        })
        resp = await adapter.chat(req)
        ended_at = self._now_iso()

        record: Dict[str, Any] = {
            "run_id": run_id,
            "provider": provider,
            "model": model,
            "conversation_id": conversation_id,
            "turn_index": turn_index,
            "state": state,
            "context_audit": ctx.get("audit", {}),
            "request": {"messages": messages},
            "response": {
                "ok": resp.ok,
                "content": resp.content,
                "latency_ms": resp.latency_ms,
                "provider_meta": resp.provider_meta,
                "error": getattr(resp, "error", None),
            },
            "timestamps": {
                "started_at": started_at,
                "ended_at": ended_at,
            },
        }
        # 4) persist artifact
        out_path = self._artifact_path(run_id, conversation_id, turn_index)
        out_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        return record
