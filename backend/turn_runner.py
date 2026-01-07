from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
import json
from datetime import datetime, timezone

try:
    from .providers.registry import ProviderRegistry
    from .providers.types import ProviderRequest
    from .state_extractor import extract_state
    from .context_builder import build_context
except ImportError:
    from providers.registry import ProviderRegistry
    from providers.types import ProviderRequest
    from state_extractor import extract_state
    from context_builder import build_context


class TurnRunner:
    def __init__(self, run_root: Path) -> None:
        self.run_root = Path(run_root)
        self.providers = ProviderRegistry()

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _artifact_path(self, run_id: str, conversation_id: str, turn_index: int) -> Path:
        base = self.run_root / run_id / "conversations" / conversation_id
        base.mkdir(parents=True, exist_ok=True)
        return base / f"turn_{turn_index:03d}.json"

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
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        started_at = self._now_iso()
        # 1) derive state from transcript
        state = extract_state(domain, turns)
        # 2) build provider-ready context
        ctx = build_context(domain, turns, state, max_tokens=max_tokens)
        messages = ctx["messages"]
        # 3) call provider
        adapter = self.providers.get(provider)
        req = ProviderRequest(model=model, messages=messages, metadata={
            "run_id": run_id,
            "conversation_id": conversation_id,
            "turn_index": turn_index,
            "domain": domain,
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
