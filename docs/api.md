# OPSCORE incident API

The API uses one startup-configured local workspace. Request parameters cannot select arbitrary filesystem paths.

## Endpoints

- `GET /api/health`
- `GET /api/incidents`
- `POST /api/incidents`
- `GET /api/incidents/{incident_id}`
- `POST /api/incidents/{incident_id}/evidence`
- `POST /api/incidents/{incident_id}/collect`
- `POST /api/incidents/{incident_id}/watch-handoff`
- `POST /api/incidents/{incident_id}/analyze`
- `GET /api/incidents/{incident_id}/analysis`
- `GET /api/incidents/{incident_id}/report.md`

## Bounded collection

`POST /api/incidents/{incident_id}/collect` accepts one explicit HTTP or HTTPS URL, one existing incident service ID, one operator-defined source location and a timeout between 0.5 and 10 seconds.

The endpoint appends DNS and HTTP evidence, plus TLS evidence for HTTPS targets. It does not follow redirects, retain response bodies, crawl links, scan ports or modify remote systems.

## WATCH handoff

`POST /api/incidents/{incident_id}/watch-handoff` accepts one `watch.opscore/v1` envelope and appends independently traceable WATCH DNS, HTTP and TLS evidence.

The endpoint rejects unknown contract versions, target references outside the incident service inventory, unsupported empty observations and duplicate WATCH run evidence. See `docs/watch-handoff.md`.

## Safety and behavior

- Incident creation rejects duplicate incident IDs with HTTP 409.
- Evidence append rejects duplicate evidence IDs with HTTP 409.
- Collection and WATCH handoff reject a `target_reference` outside the incident inventory.
- Collector URLs reject embedded credentials, fragments and invalid schemes or ports.
- Collection errors are retained as partial evidence instead of triggering broad retries.
- Duplicate WATCH run imports return HTTP 409 without modifying the incident.
- Analysis is explicit; adding, collecting or importing evidence does not run correlation.
- Bundles, analyses and reports are stored as local JSON and Markdown files.
- The API performs no DNS, network, certificate or external-system writes.
- Root-cause status remains evidence-controlled and is not automatically promoted.
