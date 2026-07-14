# Bounded TCP connectivity evidence

OPSCORE can record one explicit TCP connection attempt as incident evidence.

## Boundary

Each request contains exactly:

- one hostname or IP address;
- one TCP port from 1 to 65535;
- one existing incident service ID;
- one operator-defined source location;
- one timeout between 0.5 and 10 seconds.

The collector opens one TCP connection and immediately closes it. It sends no application payload, reads no banner, performs no authentication and does not retry neighboring hosts or ports.

## API

`POST /api/incidents/{incident_id}/connectivity`

```json
{
  "host": "orders.example.test",
  "port": 443,
  "target_reference": "orders-web",
  "source_location": "operator-laptop",
  "timeout_seconds": 3
}
```

The resulting evidence type is `tcp-connectivity`. A refused, unreachable or timed-out attempt is persisted as partial evidence rather than retried broadly.

## CLI

```powershell
python -m opscore.cli connectivity `
  --host orders.example.test `
  --port 443 `
  --target-reference orders-web `
  --source-location operator-laptop
```

The command writes `tcp-connectivity-evidence.json` to the local connectivity workspace.

## Interpretation

A successful TCP handshake proves only that a connection was established from the recorded source location at that time. It does not prove application health, protocol correctness, authentication success or end-to-end business functionality.
