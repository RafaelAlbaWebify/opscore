# Incident history

## Purpose

M8 adds an immutable local revision history for OPSCORE incidents and analyses. The history exists to show how an investigation changed over time without changing the existing current-state JSON and Markdown outputs.

The history is evidence about OPSCORE activity. It is not a backup system, restore mechanism, source-control replacement or root-cause engine.

## Storage boundary

OPSCORE creates one SQLite database inside the startup-configured workspace. Requests cannot provide or override a database path.

The existing files remain authoritative current-state outputs:

- `incidents/<incident_id>.json`
- `analyses/<incident_id>.json`
- `reports/<incident_id>.md`

SQLite stores immutable historical revisions alongside those outputs. M8 does not remove or silently rewrite existing JSON files during database bootstrap.

## Revision types

### Bundle revision

Recorded after a validated incident bundle is successfully saved.

The payload contains the full validated `IncidentBundle` JSON representation.

### Analysis revision

Recorded after an explicit analysis is successfully generated and saved.

The payload contains the full validated `IncidentAnalysis` JSON representation.

## Revision identity

Each revision belongs to one incident and has:

- incident identifier;
- monotonically increasing revision number within that incident;
- revision type: `bundle` or `analysis`;
- timezone-aware creation timestamp normalized to UTC;
- complete validated JSON payload.

Revision numbers are assigned transactionally. Existing revisions are never renumbered, overwritten or deleted by normal OPSCORE operations.

## Read-only access

M8 exposes bounded operations to:

- list revision metadata for one incident;
- retrieve one revision by incident identifier and revision number.

History reads must not update access timestamps, counters, payloads or current-state files.

The operator interface may display revision metadata and payload summaries. It must not expose restore, rollback, delete, edit or replay controls.

## Bootstrap and compatibility

Opening an existing workspace creates the SQLite schema when absent. It does not automatically invent historical revisions for pre-M8 files.

The first successful post-M8 save records the first revision for that incident. Current JSON, analysis and report loading behavior remains compatible with M0–M7.

## Safety boundaries

M8 does not:

- connect to an external or production database;
- accept arbitrary database paths from API requests;
- restore or roll back an incident;
- delete or mutate historical revisions;
- infer hypothesis progression or root cause;
- alter evidence gathered from remote systems;
- claim that SQLite history is a recoverability or backup guarantee.

## Verification requirements

Automated proof must cover:

- schema bootstrap in a new workspace;
- compatibility with an existing JSON-only workspace;
- ordered bundle and analysis revisions;
- immutable historical payloads after later saves;
- Pydantic round-trip validation;
- invalid incident and revision identifier handling;
- read-only list and retrieval behavior;
- API and OpenAPI contracts;
- Linux and Windows execution.

M8 is complete only after exact-final-head Linux and Windows CI pass and the roadmap records that proof.
