# OPSCORE incident API

The API uses one startup-configured local workspace. Request parameters cannot select arbitrary filesystem paths.

## Endpoints

- `GET /api/health`
- `GET /api/incidents`
- `POST /api/incidents`
- `GET /api/incidents/{incident_id}`
- `POST /api/incidents/{incident_id}/evidence`
- `POST /api/incidents/{incident_id}/collect`
- `POST /api/incidents/{incident_id}/analyze`
- `GET /api/incidents/{incident_id}/analysis`
- `GET /api/incidents/{incident_id}/report.md`

## Bounded collection

`POST /api/incidents/{incident_id}/collect` accepts one explicit HTTP or HTTPS URL, one existing incident service ID, one operator-defined source location and a timeout between 0.5 and 10 seconds.

The endpoint appends DNS and HTTP evidence, plus TLS evidence for HTTPS targets. It does not follow redirects, retain response bodies, crawl links, scan ports or modify remote systems.

## Safety and behavior

- Incident creation rejects duplicate incident IDs with HTTP 409.
- Evidence append rejects duplicate evidence IDs with HTTP 409.
- Collection rejects a `target_reference` that is not already part of the incident service inventory.
- Collector URLs reject embedded credentials, fragments and invalid schemes or ports.
- Collection errors are retained as partial evidence instead of triggering broad retries.
- Analysis is explicit; adding or collecting evidence does not automatically run correlation.
- Bundles, analyses and reports are stored as local JSON and Markdown files.
- The API performs no DNS, network, certificate or external-system writes.
- Root-cause status remains evidence-controlled and is not automatically promoted.
