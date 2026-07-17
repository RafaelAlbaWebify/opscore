# OPSCORE incident API

The API uses one startup-configured local workspace. Request parameters cannot select arbitrary filesystem paths.

## Endpoints

- `GET /api/health`
- `GET /api/incidents`
- `POST /api/incidents`
- `GET /api/incidents/{incident_id}`
- `POST /api/incidents/{incident_id}/evidence`
- `POST /api/incidents/{incident_id}/collect`
- `POST /api/incidents/{incident_id}/connectivity`
- `POST /api/incidents/{incident_id}/backup-awareness`
- `POST /api/incidents/{incident_id}/watch-handoff`
- `POST /api/incidents/{incident_id}/analyze`
- `GET /api/incidents/{incident_id}/analysis`
- `GET /api/incidents/{incident_id}/assessment`
- `PUT /api/incidents/{incident_id}/assessment`
- `GET /api/incidents/{incident_id}/report.md`
- `GET /api/incidents/{incident_id}/history`
- `GET /api/incidents/{incident_id}/history/{revision_number}`

## Investigation assessment

`PUT /api/incidents/{incident_id}/assessment` records one explicit operator assessment after an analysis exists. It validates the incident identifier and all referenced finding and evidence identifiers against the current persisted analysis.

A confirmed root-cause assessment requires an explicit statement, supporting evidence and no unresolved required-evidence entries. These constraints validate the record; they do not independently prove the conclusion.

`GET /api/incidents/{incident_id}/assessment` returns the current assessment. Every successful save appends an immutable assessment revision. No endpoint automatically creates hypotheses, promotes statuses or infers root cause.

## Incident history

`GET /api/incidents/{incident_id}/history` returns ordered metadata for immutable bundle, analysis and assessment revisions. `GET /api/incidents/{incident_id}/history/{revision_number}` returns one revision and its complete validated JSON payload.

History endpoints are read-only. They do not restore, roll back, edit, delete or promote any revision. Revision identifiers are bounded positive integers, incident identifiers use the existing OPSCORE contract, and the application workspace remains fixed at startup.

## Bounded collection

`POST /api/incidents/{incident_id}/collect` accepts one explicit HTTP or HTTPS URL, one existing incident service ID, one operator-defined source location and a timeout between 0.5 and 10 seconds.

The endpoint appends DNS and HTTP evidence, plus TLS evidence for HTTPS targets. It does not follow redirects, retain response bodies, crawl links, scan ports or modify remote systems.

## TCP connectivity

`POST /api/incidents/{incident_id}/connectivity` accepts one explicit hostname or IP address, one TCP port, one existing incident service ID, one source location and a timeout between 0.5 and 10 seconds.

It performs one connection attempt, sends no application payload, reads no banner and does not enumerate or retry neighboring hosts or ports.

## Backup awareness

`POST /api/incidents/{incident_id}/backup-awareness` accepts one operator-supplied backup-awareness record for an existing incident service.

The record preserves source-system and source-location provenance, a protection state, optional successful-backup and restore-test timestamps, optional RPO and RTO values, and public-safe retention or operator notes. The endpoint does not connect to a backup platform, execute jobs, change schedules or retention, perform restores, or claim recoverability.

## WATCH handoff

`POST /api/incidents/{incident_id}/watch-handoff` accepts one `watch.opscore/v1` envelope and appends independently traceable WATCH DNS, HTTP and TLS evidence.

## Safety and behavior

- Analysis is explicit; adding, collecting or importing evidence does not run correlation.
- Assessments require an existing analysis and explicit operator input.
- Unknown finding or evidence references are rejected.
- Confirmed root cause is never inferred automatically.
- Bundles, analyses, assessments and reports remain available as local current-state files.
- Successful bundle, analysis and assessment saves append immutable SQLite history revisions.
- History reads do not alter current files or database state.
- The API performs no DNS, certificate, service, backup-platform or external-system writes.
