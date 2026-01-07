import types
import asyncio
from pathlib import Path
import tempfile

import pytest

from turn_runner import TurnRunner

@pytest.mark.asyncio
async def test_turn_runner_persists(monkeypatch):
    with tempfile.TemporaryDirectory() as d:
        runner = TurnRunner(Path(d))

        # mock provider chat
        reg = runner.providers
        ollama = reg.get("ollama")
        async def fake_chat(self, req):
            return types.SimpleNamespace(ok=True, content="ok", latency_ms=2, provider_meta={})
        monkeypatch.setattr(type(ollama), "chat", fake_chat, raising=True)

        turns = [
            {"role": "user", "text": "I want a refund for order A1"},
            {"role": "assistant", "text": "We can issue refund of $10."},
        ]
        rec = await runner.run_turn(
            run_id="runx",
            provider="ollama",
            model="llama3.2:latest",
            domain="commerce",
            conversation_id="conv1",
            turn_index=1,
            turns=turns,
        )
        assert rec["response"]["ok"]
        out = Path(d) / "runx" / "conversations" / "conv1" / "turn_001.json"
        assert out.exists()
