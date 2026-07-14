# WATCH to OPSCORE handoff contract

OPSCORE accepts one versioned, read-only WATCH execution envelope at a time.

## Contract version

The current contract identifier is:

```text
watch.opscore/v1
```

Unknown versions are rejected instead of being interpreted heuristically.

## Endpoint

```text
POST /api/incidents/{incident_id}/watch-handoff
```

The incident must already exist, and `target_reference` must identify a service already present in that incident.

## Required envelope

```json
{
  "contract_version": "watch.opscore/v1",
  "target_reference": "orders-web",
  "source_location": "watch-local-runner",
  "run": {
    "run_id": "watch-run-001",
    "target_id": "orders-public",
    "started_at": "2026-07-14T10:00:00Z",
    "finished_at": "2026-07-14T10:00:02Z",
    "status": "completed",
    "observations": {
      "http_status": 503,
      "resolved_ips": ["192.0.2.10"],
      "tls_days_remaining": 18,
      "errors": []
    }
  }
}
```

See `samples/imports/watch-handoff-v1.json` for the full sample.

## Normalization

A handoff can produce independently traceable DNS, HTTP and TLS evidence items. Every item records:

- WATCH run ID;
- source location;
- contract version;
- incident service reference;
- collection completion time;
- raw WATCH reference.

## Idempotency

Evidence IDs are derived from the WATCH `run_id` and evidence type. Re-importing the same run into the same incident returns HTTP 409 and does not duplicate evidence.

## Safety boundary

The handoff endpoint only validates and stores supplied evidence. It does not execute WATCH, contact a target, schedule checks, retry collection or modify external systems. Imported observations remain evidence and never automatically become a confirmed root cause.
