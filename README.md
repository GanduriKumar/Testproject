# Multi-Turn LLM Evaluation System (MVP)

Monorepo for a multi-turn LLM evaluation platform.

- Backend: FastAPI REST API (under `backend/`)
- Frontend: React + Vite + TypeScript + Tailwind (under `frontend/`)
- Shared: `configs/`, `datasets/`, `scripts/`, `docs/`

Key MVP capabilities
- Upload JSON datasets/goldens (multiple acceptable variants per turn)
- Select LLM provider/model (Ollama llama3.2:latest, Gemini gemini-2.5)
- Configure/run evaluations with context policy (state object + last 4 turns)
- Metrics: exact, semantic (nomic-embed-text, threshold 0.80), consistency, adherence, hallucination
- Reports: per-turn diffs, CSV export, human feedback capture, simple run compare
- Persistence: filesystem only

Getting started
- See `docs/mvp-implementation-plan.md` for the step-by-step plan.
- A single dev command will be provided later to run backend and frontend.

License
- Licensed under GNU GPL v3. See `LICENSE`.
