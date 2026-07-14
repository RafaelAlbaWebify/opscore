# Evidence import contracts

## DNS Audit Tool CSV

Required columns:

```text
Zone,RecordName,RecordType,IPAddress,Finding,Severity,RecommendedAction
```

Each row becomes an independent `dns-audit-finding` evidence item. Provenance includes the source filename and row number. Missing required columns or missing finding/record names are rejected.

Imported DNS findings require service-impact validation. Missing PTR or stale-looking records do not by themselves prove an outage.

## WATCH JSON run

Required top-level fields:

```text
run_id
target_id
started_at
finished_at
status
observations
```

Supported observations are normalized separately as:

- `dns-resolution`
- `http-response`
- `tls-certificate`

WATCH timestamps must be timezone-aware. A run containing no supported observations is rejected.

## Provenance

Every imported evidence item records:

- source system;
- collection timestamp;
- OPSCORE target service;
- raw source reference;
- collection status;
- known limitations.

Adapters must reject malformed input rather than invent missing source facts.
