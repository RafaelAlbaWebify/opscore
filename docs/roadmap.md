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

- [x] Create, list and retrieve incident bundles.
- [x] Append validated evidence through a bounded endpoint.
- [x] Reject duplicate incident and evidence identifiers.
- [x] Run analysis explicitly and retrieve persisted results.
- [x] Download generated Markdown reports.
- [x] Keep the local workspace fixed at application startup.
- [x] Cover the API lifecycle and local persistence with automated tests.
- [x] Lock the public OpenAPI paths and methods with regression proof.

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
