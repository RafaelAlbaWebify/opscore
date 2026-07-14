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
- [x] Complete authoritative Linux and Windows CI proof for M3.

## M4 — Bounded live collectors

- [x] Single-target DNS evidence collection.
- [x] Single-target HTTP/service reachability collection.
- [x] TLS certificate evidence collection for HTTPS targets.
- [x] Explicit timeouts and source-location provenance.
- [x] Collector URL and credential safety validation.
- [x] Partial evidence for bounded collection failures.
- [x] Incident API endpoint for explicit collection.
- [x] One-off CLI collection and JSON export.
- [x] Collector safety and network-boundary tests.
- [x] Complete authoritative Linux and Windows CI proof for M4.

## M5 — WATCH handoff contract

- [x] Versioned `watch.opscore/v1` handoff envelope.
- [x] Explicit WATCH source-location and run provenance.
- [x] DNS, HTTP and TLS evidence normalization.
- [x] Incident API handoff endpoint.
- [x] Incident-service validation.
- [x] Duplicate WATCH run protection.
- [x] Unsupported-observation rejection.
- [x] Public sample payload and integration documentation.
- [x] OpenAPI and lifecycle regression tests.
- [x] Complete authoritative Linux and Windows CI proof for M5.

## M6 — Bounded TCP connectivity evidence

- [x] One explicit hostname or IP address and one explicit TCP port.
- [x] Fixed timeout between 0.5 and 10 seconds.
- [x] Read-only connection attempt without application payloads.
- [x] Source-location and elapsed-time provenance.
- [x] Partial evidence for refused, unreachable and timed-out connections.
- [x] Incident API endpoint and service validation.
- [x] One-off CLI JSON export.
- [x] Deterministic offline socket tests.
- [ ] Complete authoritative Linux and Windows CI proof for M6.

## Deferred

- SQLite incident history.
- Backup-awareness evidence.
- Hypothesis progression and final RCA workflow.

Automatic remediation, broad scanning and production writes remain out of scope.
