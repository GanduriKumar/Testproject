import asyncio
import json
from pathlib import Path
import tempfile
import types

import pytest

from orchestrator import Orchestrator

@pytest.mark.asyncio
async def test_orchestrator_happy_path(monkeypatch):
    with tempfile.TemporaryDirectory() as d:
        ds_dir = Path(d, 'datasets'); ds_dir.mkdir()
        runs_dir = Path(d, 'runs'); runs_dir.mkdir()
        # dataset
        ds = {
            "dataset_id": "commerce_sample",
            "version": "1.0.0",
            "metadata": {"domain": "commerce", "difficulty": "easy"},
            "conversations": [
                {
                    "conversation_id": "c1",
                    "turns": [
                        {"role": "user", "text": "Where is my order A1?"},
                        {"role": "assistant", "text": "Share order ID"},
                        {"role": "user", "text": "It is A1"}
                    ]
                }
            ]
        }
        Path(ds_dir, 'commerce_sample.dataset.json').write_text(json.dumps(ds), encoding='utf-8')

        orch = Orchestrator(datasets_dir=ds_dir, runs_root=runs_dir)
        # mock runner.run_turn to avoid network
        async def fake_run_turn(self, **kwargs):
            return {"response": {"ok": True}}
        monkeypatch.setattr(type(orch._runner), 'run_turn', fake_run_turn, raising=True)

        jr = orch.submit(dataset_id='commerce_sample', model_spec='ollama:llama3.2:latest', config={"metrics": ["exact"], "thresholds": {}})
        orch.start(jr.job_id)
        res = await orch.wait(jr.job_id)
        assert res.state == 'succeeded'
        assert res.progress_pct == 100
        # confirm artifacts folder
        run_folder = Path(runs_dir, jr.run_id)
        assert run_folder.exists()

@pytest.mark.asyncio
async def test_orchestrator_cancel(monkeypatch):
    with tempfile.TemporaryDirectory() as d:
        ds_dir = Path(d, 'datasets'); ds_dir.mkdir()
        runs_dir = Path(d, 'runs'); runs_dir.mkdir()
        ds = {
            "dataset_id": "commerce_sample",
            "version": "1.0.0",
            "metadata": {"domain": "commerce", "difficulty": "easy"},
            "conversations": [
                {"conversation_id": "c1", "turns": [{"role": "user", "text": "hi"}, {"role": "assistant", "text": "hello"}]},
                {"conversation_id": "c2", "turns": [{"role": "user", "text": "hi"}, {"role": "assistant", "text": "hello"}]}
            ]
        }
        Path(ds_dir, 'commerce_sample.dataset.json').write_text(json.dumps(ds), encoding='utf-8')

        orch = Orchestrator(datasets_dir=ds_dir, runs_root=runs_dir)
        async def slow_run_turn(self, **kwargs):
            await asyncio.sleep(0.01)
            return {"response": {"ok": True}}
        monkeypatch.setattr(type(orch._runner), 'run_turn', slow_run_turn, raising=True)

        jr = orch.submit(dataset_id='commerce_sample', model_spec='ollama:llama3.2:latest', config={})
        orch.start(jr.job_id)
        orch.cancel(jr.job_id)
        res = await orch.wait(jr.job_id)
        assert res.state == 'cancelled'
