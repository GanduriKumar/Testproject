# Coverage Governance & Versioning

This document describes how to manage the coverage taxonomy and exclusion rules.

Files
- configs/taxonomy.json — domains, behaviors, and axis value bins.
- configs/exclusions.json — exclusion and capping rules that constrain scenario space.
- configs/schemas/*.schema.json — JSON Schemas for validation.

Versioning
- Add an optional `version` field to taxonomy and exclusions files, e.g. "version": "2026.01".
- Bump the version when you change any domain, behavior, axis bins, or rules.
- Reference the version in PRs and release notes.

Linting & Validation
- On load, the backend performs governance lint checks (backend/coverage_config.py):
  - Duplicate detection in domains, behaviors, and axis values.
  - Conflict detection for rules that target the same applies + when but mix exclude and cap.
- Breaking changes should include updates to the test suite.

Change process
- Prefer additive changes first (new behaviors or axes) and avoid renaming unless necessary.
- For deletions/renames, provide a migration note and update tests/manifests.
- Document rationale in each rule’s notes field.

Testing
- Run pytest and ensure coverage tests pass.
- Dry‑run the coverage CLI: python -m backend.cli coverage --dry-run --combined --save (with or without filters).
- Validate generated datasets/goldens using the schemas.

Rollout
- If you change the taxonomy significantly, coordinate with the UI to reflect labels.
- Communicate version bumps to all users.
