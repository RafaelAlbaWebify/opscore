# OPSCORE incident API

The API uses one startup-configured local workspace. Request parameters cannot select arbitrary filesystem paths.

## Endpoints

- `GET /api/health`
- `GET /api/incidents`
- `POST /api/incidents`
- `GET /api/incidents/{incident_id}`
- `POST /api/incidents/{incident_id}/evidence`
- `POST /api/incidents/{incident_id}/analyze`
- `GET /api/incidents/{incident_id}/analysis`
- `GET /api/incidents/{incident_id}/report.md`

## Safety and behavior

- Incident creation rejects duplicate incident IDs with HTTP 409.
- Evidence append rejects duplicate evidence IDs with HTTP 409.
- Analysis is explicit; adding evidence does not automatically run correlation.
- Bundles, analyses and reports are stored as local JSON and Markdown files.
- The API performs no DNS, network, certificate or external-system writes.
- Root-cause status remains evidence-controlled and is not automatically promoted.
