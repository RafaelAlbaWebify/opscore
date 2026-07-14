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
- [x] Add explicit OpenAPI path and method regression proof.

## M3 — Operator interface

- [x] Responsive local operator workbench.
- [x] Incident intake using the validated API contract.
- [x] Incident list and selection.
- [x] Service and dependency views.
- [x] Evidence inventory.
- [x] Timeline, findings, missing evidence and safe-check views.
- [x] Explicit analysis execution.
- [x] Markdown report preview.
- [x] Output escaping for user-controlled values.
- [x] Path-independent Windows UI launcher.
- [x] Playwright functional workflow and screenshot artifact.
- [ ] Complete authoritative Linux and Windows CI proof for M3.

## M4 — Bounded live collectors

- [ ] Single-target DNS evidence collection.
- [ ] Single-target HTTP/service reachability collection.
- [ ] TLS certificate evidence collection.
- [ ] Explicit timeouts and source-location provenance.
- [ ] Collector safety and network-boundary tests.

## Deferred

- SQLite incident history.
- WATCH-to-OPSCORE handoff contract.
- Port/connectivity evidence.
- Backup-awareness evidence.
- Hypothesis progression and final RCA workflow.

Automatic remediation, broad scanning and production writes remain out of scope.
