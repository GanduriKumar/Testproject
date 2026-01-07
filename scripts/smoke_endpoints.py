import os
import sys
import time
from pathlib import Path

# Ensure project root is on sys.path so 'backend' package is importable
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
import httpx

# Import the app from backend package
from backend.app import app


def main():
    client = TestClient(app)

    # Health
    r = client.get('/health')
    print('GET /health', r.status_code, r.json())

    # Version
    r = client.get('/version')
    print('GET /version', r.status_code, r.json())

    # Datasets
    r = client.get('/datasets')
    print('GET /datasets', r.status_code, r.json())

    # Conversation fetch
    r = client.get('/conversations/conv1')
    print('GET /conversations/conv1', r.status_code)

    # Start a run
    # Detect available Ollama models and embeddings
    ollama = os.getenv('OLLAMA_HOST', 'http://localhost:11434').rstrip('/')
    model = 'llama3.2:latest'
    have_embed = False
    try:
        with httpx.Client(timeout=5.0) as hc:
            r = hc.get(f"{ollama}/api/tags")
            if r.status_code == 200:
                tags = r.json().get('models', [])
                names = [m.get('name') for m in tags]
                # Prefer llama3.2:latest, else any llama*, else first
                if 'llama3.2:latest' in names:
                    model = 'llama3.2:latest'
                else:
                    cand = next((n for n in names if isinstance(n, str) and n.startswith('llama')), None)
                    if cand:
                        model = cand
                    elif names:
                        model = names[0]
                have_embed = any(n == 'nomic-embed-text' for n in names)
    except Exception:
        pass

    metrics = ["exact"] + (["semantic"] if have_embed else [])
    body = {
        "dataset_id": "demo",
        "model_spec": f"ollama:{model}",
        "metrics": metrics,
        "thresholds": {"semantic": 0.80},
    }
    r = client.post('/runs', json=body)
    print('POST /runs', r.status_code, r.json())
    assert r.status_code == 200, 'Failed to start run'
    job_id = r.json()['job_id']
    run_id = r.json()['run_id']

    # Poll status
    t0 = time.time()
    while True:
        rs = client.get(f'/runs/{job_id}/status')
        js = rs.json()
        print('STATUS', js)
        if js['state'] in ('succeeded', 'failed', 'cancelled'):
            break
        if time.time() - t0 > 30:
            print('Timeout waiting for run to finish')
            break
        time.sleep(0.5)

    # Check artifacts folder exists
    runs_root = Path(__file__).resolve().parents[1] / 'runs'
    conv_dir = runs_root / run_id / 'conversations' / 'conv1'
    if conv_dir.exists():
        files = sorted(p.name for p in conv_dir.glob('*.json'))
        print('Turn artifacts:', files)
    else:
        print('No conversation artifacts found at', conv_dir)

    # Try results endpoints (may 404 if results.json not generated yet)
    rr = client.get(f'/runs/{run_id}/results')
    print('GET /runs/{}/results ->'.format(run_id), rr.status_code)
    ar_csv = client.get(f'/runs/{run_id}/artifacts', params={'type': 'csv'})
    print('GET /runs/{}/artifacts?type=csv ->'.format(run_id), ar_csv.status_code)
    ar_html = client.get(f'/runs/{run_id}/artifacts', params={'type': 'html'})
    print('GET /runs/{}/artifacts?type=html ->'.format(run_id), ar_html.status_code)


if __name__ == '__main__':
    main()
