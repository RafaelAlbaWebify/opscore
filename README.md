# OPSCORE

> Infrastructure and production operations incident evidence workbench.

OPSCORE is a local-first, read-only workbench for correlating infrastructure and production-service evidence around an incident. It imports public-safe DNS Audit Tool CSV evidence and versioned WATCH handoffs, performs bounded single-target DNS/HTTP/TLS and TCP-connectivity checks, records operator-supplied backup-awareness context, normalizes source provenance, applies deterministic correlation rules, and presents support-ready findings, timelines, missing evidence, safe next checks, and reports through an API, CLI, and local operator interface.

## Portfolio purpose

OPSCORE is Rafael Alba's flagship project for the **Infrastructure / Production Operations Engineer** path.

It is deliberately separated from:

- **WATCH**, which controls recurring operational checks, changes and actions.
- **TRACE**, which structures IAM and access evidence.
- **CustosOps**, which structures defensive security evidence.
- **DNS Audit Tool**, which remains a specialist OPSCORE evidence provider.

## Current capability

```text
incident and service context
+ DNS Audit Tool CSV
+ versioned WATCH handoff
+ one explicit DNS/HTTP/TLS target
+ one explicit TCP endpoint
+ operator-supplied backup-awareness metadata
→ source validation and provenance
→ normalized evidence
→ cross-source correlation
→ timeline, findings and missing evidence
→ local incident persistence and bounded API
→ operator workbench and Markdown/JSON reports
```

Current deterministic findings include:

- successful DNS resolution with failed HTTP reachability;
- contradictory availability evidence;
- forward/reverse DNS consistency requiring review;
- TLS certificate expiry risk;
- missing evidence for required dependencies.

OPSCORE does not claim root cause unless the available evidence explicitly supports that conclusion. Backup-awareness metadata does not independently prove recoverability or restore success.

## Quick start

```powershell
.\OPSCORE.ps1 setup
.\OPSCORE.ps1 verify
.\OPSCORE.ps1 demo
.\OPSCORE.ps1 correlate
.\OPSCORE.ps1 ui
.\OPSCORE.ps1 export
```

`OPSCORE.ps1 ui` opens the local operator workbench at `http://127.0.0.1:8000`. The launcher resolves the repository root from its own path, so it can be called from any PowerShell working directory.

Direct Python commands:

```powershell
python -m opscore.cli demo --workspace .opscore-data
python -m opscore.cli correlate --workspace .opscore-data\imported
python -m opscore.cli collect --url https://example.test/health `
  --target-reference service-web --source-location operator-laptop
python -m opscore.cli connectivity --host example.test --port 443 `
  --target-reference service-web --source-location operator-laptop
python -m opscore.cli watch-handoff `
  --handoff-file samples/imports/watch-handoff-v1.json
python -m uvicorn opscore.api:app --host 127.0.0.1 --port 8000
```

## WATCH handoff

M5 defines the explicit `watch.opscore/v1` contract between WATCH and OPSCORE. One handoff carries a WATCH run, incident service reference and source location. OPSCORE validates the version, normalizes DNS/HTTP/TLS observations, preserves run provenance and rejects duplicate run imports.

See `docs/watch-handoff.md` and `samples/imports/watch-handoff-v1.json`.

## Bounded collection

M4 collects read-only evidence for one explicit HTTP or HTTPS URL at a time:

- DNS resolution for the supplied hostname;
- one HTTP GET without redirect following or response-body retention;
- one TLS handshake for HTTPS targets;
- a fixed timeout between 0.5 and 10 seconds;
- operator-defined source-location provenance;
- partial evidence when a bounded operation fails.

M6 adds one explicit TCP-connectivity attempt for one hostname or IP address and one port. It sends no application payload, reads no banner and does not scan adjacent hosts or ports.

It does not crawl, scan port ranges, enumerate neighboring hosts, retry broadly or modify remote systems. See `docs/collectors.md` and `docs/connectivity.md`.

## Backup awareness

M7 records structured backup-awareness metadata supplied by an operator for one existing incident service. It preserves protection state, timestamps, RPO/RTO context, retention summary, notes and source provenance.

OPSCORE does not connect to backup platforms, control jobs, change schedules or retention, perform restores, or infer recoverability from this metadata. See `docs/backup-awareness.md`.

## Operator workbench

The local interface provides:

- validated incident intake;
- incident list and selection;
- service and dependency views;
- evidence inventory;
- explicit deterministic analysis;
- timeline, findings, missing evidence and safe next checks;
- Markdown report preview.

User-controlled values are escaped before HTML rendering. The interface writes only to the configured local OPSCORE workspace.

## Developer workflow

After the repository is cloned, future branches can be synchronized and verified from any PowerShell working directory:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File C:\Users\ralba\source\repos\opscore\scripts\github-workflow.ps1 `
  verify-pr agent/example-branch
```

The script performs a normal authenticated push, waits for pull-request CI, prints Linux and Windows job results and saves failed logs to `C:\Users\ralba\Downloads`.

## Automated proof

The repository is configured to run on Linux and Windows:

- Ruff linting;
- strict mypy checks;
- pytest with an enforced 85% coverage minimum;
- deterministic demo generation;
- DNS CSV and WATCH evidence correlation;
- WATCH handoff contract and duplicate-run tests;
- bounded collector and TCP-connectivity safety tests;
- backup-awareness contract and API lifecycle tests;
- PowerShell operator verification;
- Playwright browser workflow with a screenshot artifact;
- review artifact generation.

## Safety boundary

OPSCORE is read-only first. It does not modify DNS, certificates, services, backup platforms, remote systems or production infrastructure. Public repository data must remain synthetic or sanitized.

See `docs/safety-boundaries.md` for the full boundary.
