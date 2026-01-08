import json
import pytest
import httpx

from backend.app import app


@pytest.mark.anyio
async def test_coverage_generate_dry_run_combined():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/coverage/generate", json={
            "combined": True,
            "dry_run": True,
            "save": False,
            "version": "1.0.0"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["saved"] is False
        assert isinstance(data["outputs"], list)
        assert len(data["outputs"]) >= 2  # at least domain combined + global combined


@pytest.mark.anyio
async def test_coverage_generate_save_split_overwrite(tmp_path, monkeypatch):
    # Redirect datasets root to a temp dir via DatasetRepository init in Orchestrator
    from backend.dataset_repo import DatasetRepository
    from backend.orchestrator import Orchestrator

    # Monkeypatch orch to use temp dir
    orch = Orchestrator(runs_root=tmp_path / "runs")
    app.state.orch = orch

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/coverage/generate", json={
            "combined": False,
            "dry_run": False,
            "save": True,
            "overwrite": True,
            "version": "1.0.0",
            "domains": ["Returns, Refunds & Exchanges"],
            "behaviors": ["Happy Path"]
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["saved"] is True
        files = data["files"]
        assert isinstance(files, list) and len(files) >= 1
