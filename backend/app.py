from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Any, Dict, Optional
import os
from pathlib import Path

from dataset_repo import DatasetRepository
from orchestrator import Orchestrator
from artifacts import RunArtifactWriter, RunArtifactReader
from reporter import Reporter

APP_VERSION = "0.1.0-mvp"

class Health(BaseModel):
    status: str

class VersionInfo(BaseModel):
    version: str
    gemini_enabled: bool
    ollama_host: str | None
    semantic_threshold: float


def get_settings():
    google_api_key = os.getenv("GOOGLE_API_KEY")
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    semantic_threshold = float(os.getenv("SEMANTIC_THRESHOLD", "0.80"))
    return {
        "GOOGLE_API_KEY": google_api_key,
        "OLLAMA_HOST": ollama_host,
        "SEMANTIC_THRESHOLD": semantic_threshold,
    }

app = FastAPI(title="LLM Eval Backend", version=APP_VERSION)

# App state singletons
RUNS_ROOT = Path(__file__).resolve().parents[1] / "runs"
RUNS_ROOT.mkdir(parents=True, exist_ok=True)
app.state.orch = Orchestrator(runs_root=RUNS_ROOT)
app.state.artifacts = RunArtifactWriter(RUNS_ROOT)
app.state.reader = RunArtifactReader(RUNS_ROOT)
app.state.reporter = Reporter(Path(__file__).resolve().parent / "templates")


class StartRunRequest(BaseModel):
    dataset_id: str
    model_spec: str  # e.g., "ollama:llama3.2:2b" or "gemini:gemini-2.5"
    metrics: Optional[list[str]] = None
    thresholds: Optional[dict[str, Any]] = None
    context: Optional[dict[str, Any]] = None

class StartRunResponse(BaseModel):
    job_id: str
    run_id: str
    state: str

@app.get("/health", response_model=Health)
async def health():
    return Health(status="ok")

@app.get("/version", response_model=VersionInfo)
async def version():
    s = get_settings()
    return VersionInfo(
        version=APP_VERSION,
        gemini_enabled=bool(s["GOOGLE_API_KEY"]),
        ollama_host=s["OLLAMA_HOST"],
        semantic_threshold=s["SEMANTIC_THRESHOLD"],
    )


@app.get("/datasets")
async def list_datasets():
    repo: DatasetRepository = app.state.orch.repo
    return repo.list_datasets()


@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    repo: DatasetRepository = app.state.orch.repo
    conv = repo.get_conversation(conversation_id)
    try:
        golden = repo.get_golden(conversation_id)
    except Exception:
        golden = None
    return {"conversation": conv, "golden": golden}


@app.post("/runs", response_model=StartRunResponse)
async def start_run(req: StartRunRequest):
    orch: Orchestrator = app.state.orch
    cfg: Dict[str, Any] = {
        "metrics": req.metrics or [],
        "thresholds": req.thresholds or {},
        "context": req.context or {},
    }
    jr = orch.submit(dataset_id=req.dataset_id, model_spec=req.model_spec, config=cfg)
    # initialize run folder with config
    app.state.artifacts.init_run(jr.run_id, {"dataset_id": req.dataset_id, "model_spec": req.model_spec, **cfg})
    orch.start(jr.job_id)
    return StartRunResponse(job_id=jr.job_id, run_id=jr.run_id, state=jr.state)


@app.get("/runs/{job_id}/status")
async def run_status(job_id: str):
    orch: Orchestrator = app.state.orch
    jr = orch.jobs.get(job_id)
    if not jr:
        raise HTTPException(status_code=404, detail="job not found")
    return {
        "job_id": jr.job_id,
        "run_id": jr.run_id,
        "state": jr.state,
        "progress_pct": jr.progress_pct,
        "total_conversations": jr.total_conversations,
        "completed_conversations": jr.completed_conversations,
        "error": jr.error,
    }


@app.get("/runs/{run_id}/results")
async def run_results(run_id: str):
    reader: RunArtifactReader = app.state.reader
    path = reader.layout.results_json_path(run_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="results not found")
    return get_json_file(path)


def get_json_file(path: Path):
    import json
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/runs/{run_id}/artifacts")
async def run_artifacts(run_id: str, type: str = "json"):
    reader: RunArtifactReader = app.state.reader
    reporter: Reporter = app.state.reporter
    if type == "json":
        path = reader.layout.results_json_path(run_id)
        if not path.exists():
            raise HTTPException(status_code=404, detail="results.json not found")
        return FileResponse(str(path), media_type="application/json", filename="results.json")
    elif type == "csv":
        path = reader.layout.results_csv_path(run_id)
        if not path.exists():
            raise HTTPException(status_code=404, detail="results.csv not found")
        return FileResponse(str(path), media_type="text/csv", filename="results.csv")
    elif type == "html":
        # generate on the fly from results.json
        json_path = reader.layout.results_json_path(run_id)
        if not json_path.exists():
            raise HTTPException(status_code=404, detail="results.json not found")
        results = get_json_file(json_path)
        try:
            html = reporter.render_html(results)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"cannot render html: {e}")
        out_path = reader.layout.run_dir(run_id) / "report.html"
        out_path.write_text(html, encoding="utf-8")
        return FileResponse(str(out_path), media_type="text/html", filename="report.html")
    else:
        raise HTTPException(status_code=400, detail="unknown type")


@app.post("/runs/{run_id}/feedback")
async def submit_feedback(run_id: str, body: Dict[str, Any]):
    # Append feedback objects to runs/<run_id>/feedback.json
    run_dir = app.state.reader.layout.run_dir(run_id)
    fb_path = run_dir / "feedback.json"
    arr: list = []
    if fb_path.exists():
        try:
            import json
            arr = json.loads(fb_path.read_text(encoding="utf-8"))
            if not isinstance(arr, list):
                arr = []
        except Exception:
            arr = []
    arr.append(body)
    fb_path.write_text(json.dumps(arr, indent=2), encoding="utf-8")
    return {"ok": True, "count": len(arr)}


@app.get("/compare")
async def compare_runs(runA: str, runB: str):
    reader: RunArtifactReader = app.state.reader
    a = reader.layout.results_json_path(runA)
    b = reader.layout.results_json_path(runB)
    if not a.exists() or not b.exists():
        raise HTTPException(status_code=404, detail="one or both results.json missing")
    A = get_json_file(a)
    B = get_json_file(b)

    def summarize(res: Dict[str, Any]):
        convs = res.get("conversations", []) or []
        total = len(convs)
        passed = sum(1 for c in convs if c.get("summary", {}).get("conversation_pass") is True)
        rate = (passed / total) if total else 0.0
        return {"total": total, "passed": passed, "pass_rate": rate}

    SA = summarize(A)
    SB = summarize(B)
    delta = SB["pass_rate"] - SA["pass_rate"]
    return {"runA": SA, "runB": SB, "delta_pass_rate": delta}

