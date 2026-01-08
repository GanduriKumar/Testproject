import subprocess
import sys
from pathlib import Path


def run_cli(args, cwd):
    exe = [sys.executable, "-m", "backend.cli"]
    return subprocess.run(exe + args, cwd=cwd, capture_output=True, text=True)


def test_cli_coverage_dry_run(tmp_path):
    # Copy minimal workspace structure
    (tmp_path / "datasets").mkdir(parents=True, exist_ok=True)
    (tmp_path / "runs").mkdir(parents=True, exist_ok=True)

    repo_root = Path(__file__).resolve().parents[2]
    r = run_cli(["coverage", "--dry-run", "--combined", "--root", str(tmp_path)], cwd=str(repo_root))
    assert r.returncode == 0, r.stderr
    out = r.stdout
    assert "DATASET ID" in out


def test_cli_coverage_save_split(tmp_path):
    (tmp_path / "datasets").mkdir(parents=True, exist_ok=True)
    (tmp_path / "runs").mkdir(parents=True, exist_ok=True)

    repo_root = Path(__file__).resolve().parents[2]
    r = run_cli([
        "coverage", "--split", "--save", "--overwrite", "--root", str(tmp_path),
        "--domains", "Returns, Refunds & Exchanges", "--behaviors", "Happy Path"
    ], cwd=str(repo_root))
    assert r.returncode == 0, r.stderr
    # expect at least one dataset/golden written
    files = list((tmp_path / "datasets").glob("*.dataset.json"))
    assert len(files) >= 1
