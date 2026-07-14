# Bounded live collectors

OPSCORE M4 adds read-only DNS, HTTP and TLS evidence collection for one explicit target at a time.

## Safety boundary

A collection request must contain one `http` or `https` URL, one incident service ID, one operator-defined source location and a timeout between 0.5 and 10 seconds.

The collector:

- resolves only the hostname contained in the supplied URL;
- performs one HTTP GET without following redirects;
- does not download or retain the response body;
- performs one TLS handshake only for HTTPS targets;
- records errors as partial evidence rather than retrying broadly;
- does not crawl links, scan ports, enumerate hosts or modify remote systems;
- rejects embedded credentials, URL fragments and invalid ports.

## CLI

```powershell
python -m opscore.cli collect `
  --url https://example.test/health `
  --target-reference service-web `
  --source-location operator-laptop `
  --timeout-seconds 5
```

Evidence is written to `.opscore-data/collected/bounded-evidence.json` unless another workspace is supplied.

## Incident API

```text
POST /api/incidents/{incident_id}/collect
```

Example body:

```json
{
  "url": "https://example.test/health",
  "target_reference": "service-web",
  "source_location": "operator-laptop",
  "timeout_seconds": 5
}
```

The `target_reference` must already exist in the incident service inventory. Collected evidence is appended to the local incident bundle and can then be analyzed through the existing explicit analysis endpoint.

## Evidence produced

- `dns-resolution`
- `http-response`
- `tls-certificate` for HTTPS targets

Every item includes the requested URL, source location, configured timeout, collection timestamp and any stated limitations.
