# Contributing

Thanks for helping improve the Multi‑Turn LLM Evaluation System.

Commit style
- Use Conventional Commits, e.g. `feat(coverage): add manifest breakdown`.

Python (backend)
- Format: Black + isort. Lint: ruff (or flake8). Test: pytest.
- Run all tests before pushing. Add tests for new behaviors and bug fixes.
- Avoid Windows `--reload` for uvicorn during development.

Frontend (React/Vite)
- Format: Prettier. Lint: ESLint. Test: Vitest + React Testing Library.
- Keep UI components accessible (labels, roles, keyboard nav).

Coverage governance (Prompt 13)
- Taxonomy and exclusions live in `configs/taxonomy.json` and `configs/exclusions.json`.
- Version fields are allowed: add/bumps as needed (e.g., `"version": "2026.01"`).
- Lint rules run at load time (backend/coverage_config.py):
	- No duplicate domains/behaviors/axis values.
	- No conflicting rules that both set `exclude` and `cap` for the same applies/when scope.
- When changing rules:
	1) Explain rationale in the rule `notes`.
	2) Keep rule names stable; update version.
	3) Run tests and validate sample generation via CLI: `python -m backend.cli coverage --dry-run`.

Docs & User Guide
- Update `UserGuide.md` when adding user‑visible features (new pages, endpoints, or CSVs).

Opening changes
- Open an issue before large changes. Describe scope, risks, and rollout plan.
