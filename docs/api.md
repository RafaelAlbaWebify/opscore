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
- `GET /api/incidents/{incident_id}/report.md`
- `GET /api/incidents/{incident_id}/history`
- `GET /api/incidents/{incident_id}/history/{revision_number}`

## Incident history

`GET /api/incidents/{incident_id}/history` returns ordered metadata for immutable bundle and analysis revisions. `GET /api/incidents/{incident_id}/history/{revision_number}` returns one revision and its complete validated JSON payload.

History endpoints are read-only. They do not restore, roll back, edit, delete or promote any revision. Revision identifiers are bounded positive integers, incident identifiers use the existing OPSCORE contract, and the application workspace remains fixed at startup. See `docs/incident-history.md`.

## Bounded collection

`POST /api/incidents/{incident_id}/collect` accepts one explicit HTTP or HTTPS URL, one existing incident service ID, one operator-defined source location and a timeout between 0.5 and 10 seconds.

The endpoint appends DNS and HTTP evidence, plus TLS evidence for HTTPS targets. It does not follow redirects, retain response bodies, crawl links, scan ports or modify remote systems.

## TCP connectivity

`POST /api/incidents/{incident_id}/connectivity` accepts one explicit hostname or IP address, one TCP port, one existing incident service ID, one source location and a timeout between 0.5 and 10 seconds.

It performs one connection attempt, sends no application payload, reads no banner and does not enumerate or retry neighboring hosts or ports. See `docs/connectivity.md`.

## Backup awareness

`POST /api/incidents/{incident_id}/backup-awareness` accepts one operator-supplied backup-awareness record for an existing incident service.

The record preserves source-system and source-location provenance, a protection state, optional successful-backup and restore-test timestamps, optional RPO and RTO values, and public-safe retention or operator notes. A `protected` record requires a timezone-aware successful-backup timestamp. The endpoint does not connect to a backup platform, execute jobs, change schedules or retention, perform restores, or claim recoverability. See `docs/backup-awareness.md`.

## WATCH handoff

`POST /api/incidents/{incident_id}/watch-handoff` accepts one `watch.opscore/v1` envelope and appends independently traceable WATCH DNS, HTTP and TLS evidence.

The endpoint rejects unknown contract versions, target references outside the incident service inventory, unsupported empty observations and duplicate WATCH run evidence. See `docs/watch-handoff.md`.

## Safety and behavior

- Incident creation rejects duplicate incident IDs with HTTP 409.
- Evidence append rejects duplicate evidence IDs with HTTP 409.
- Collection, connectivity, backup awareness and WATCH handoff reject targets outside the incident inventory.
- Collector URLs reject embedded credentials, fragments and invalid schemes or ports.
- TCP connectivity rejects URLs, paths, target lists and invalid ports.
- Collection errors are retained as partial evidence instead of triggering broad retries.
- Unknown backup protection state is retained as partial evidence.
- Backup-awareness metadata is not treated as independent proof of backup success, restore success or recoverability.
- Duplicate WATCH run imports return HTTP 409 without modifying the incident.
- Analysis is explicit; adding, collecting or importing evidence does not run correlation.
- Bundles, analyses and reports remain available as local JSON and Markdown current-state files.
- Successful bundle and explicit analysis saves append immutable SQLite history revisions.
- History reads do not alter current files or database state.
- The API performs no DNS, certificate, service, backup-platform or external-system writes.
- Root-cause status remains evidence-controlled and is not automatically promoted.
