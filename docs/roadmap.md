# OPSCORE roadmap

## M0 — Engineering baseline

- [x] Product and safety boundary.
- [x] Python package, CLI and health API.
- [x] Explicit incident evidence domain model.
- [x] Deterministic demo and reports.
- [x] Ruff, strict mypy, pytest and coverage threshold.
- [x] Linux and Windows CI definitions.
- [x] Windows setup, verify, demo, correlation and export scripts.

## M1 — Imported evidence correlation

- [x] DNS Audit Tool CSV adapter.
- [x] WATCH JSON run adapter.
- [x] Evidence provenance and source validation.
- [x] Incident timeline.
- [x] DNS/HTTP/TLS/dependency correlation rules.
- [x] Contradictory and missing-evidence reporting.
- [x] Markdown and JSON incident reports.

## M2 — Incident API

- [ ] Create and retrieve incident bundles.
- [ ] Import evidence through bounded API endpoints.
- [ ] Run analysis and retrieve findings/timeline.
- [ ] Download reports.
- [ ] OpenAPI contract tests.

## M3 — Operator interface

- [ ] Incident intake.
- [ ] Evidence inventory.
- [ ] Dependency view.
- [ ] Timeline, findings and missing evidence.
- [ ] Report preview.
- [ ] Playwright functional and visual proof.

## Deferred

- Live bounded collectors.
- SQLite incident history.
- WATCH-to-OPSCORE handoff contract.
- Port/connectivity evidence.
- Backup-awareness evidence.
- Hypothesis progression and final RCA workflow.

Automatic remediation, broad scanning and production writes remain out of scope.
