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
- [x] Complete authoritative Linux and Windows CI proof for M6.

## M7 — Backup-awareness evidence

- [x] Structured operator-supplied backup-awareness contract.
- [x] Protected, degraded, unprotected and unknown protection states.
- [x] Timezone-aware successful-backup and restore-test timestamps.
- [x] Optional RPO, RTO, retention summary and public-safe notes.
- [x] Source-system and source-location provenance.
- [x] Protected-status validation requiring successful-backup evidence.
- [x] Partial evidence for unknown protection state.
- [x] Incident API endpoint and service validation.
- [x] OpenAPI, contract and API lifecycle regression tests.
- [x] Explicit backup-administration and recoverability safety boundary.
- [x] Complete authoritative Linux and Windows CI proof for the final M7 head.

## M8 — SQLite-backed immutable incident history

- [x] Local SQLite history database inside the configured workspace.
- [x] Immutable bundle revisions for incident creation and change.
- [x] Immutable analysis revisions for every explicit analysis run.
- [x] Deterministic per-incident revision numbers and timezone-aware timestamps.
- [x] Validated full JSON payload retained for every revision.
- [x] Existing current JSON bundles, analyses and Markdown reports preserved.
- [x] Read-only service methods for revision listing and retrieval.
- [x] Bounded read-only incident-history API endpoints.
- [x] Read-only operator-interface history visibility.
- [x] Automatic database bootstrap without modifying existing incident JSON.
- [x] Persistence, immutability, schema, CLI, OpenAPI and lifecycle regression tests.
- [x] Architecture, API, README, safety and version documentation.
- [x] Complete authoritative Linux and Windows CI proof for the final M8 implementation head.

## M9 — Evidence-backed hypothesis and RCA workflow

- [x] Explicit hypothesis and root-cause assessment contracts.
- [x] Timezone-aware operator identity and rationale fields.
- [x] Confirmed root-cause guard requiring supporting evidence and no unresolved gaps.
- [x] Validation against existing incident finding and evidence identifiers.
- [x] Current local assessment persistence.
- [x] Immutable assessment revisions integrated with M8 history.
- [x] Bounded assessment create/update and read API endpoints.
- [x] Operator-interface hypothesis and root-cause visibility.
- [x] Report integration that keeps deterministic findings separate from operator assessment.
- [x] Persistence, migration, API, OpenAPI and lifecycle regression tests.
- [x] Architecture, API, README, safety and version documentation.
- [ ] Complete authoritative Linux and Windows CI proof for the final M9 head.

Automatic hypothesis generation, root-cause inference, remediation, broad scanning, history rollback, revision deletion and production writes remain out of scope.
