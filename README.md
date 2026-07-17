# OPSCORE

> Infrastructure and production operations incident evidence workbench.

OPSCORE **v0.9.0** is a local-first, read-only workbench for correlating infrastructure and production-service evidence around an incident. It imports public-safe DNS Audit Tool CSV evidence and versioned WATCH handoffs, performs bounded single-target DNS/HTTP/TLS and TCP-connectivity checks, records operator-supplied backup-awareness context, applies deterministic correlation rules, preserves immutable incident revisions, and records explicit evidence-backed operator assessments through an API, CLI, reports and local operator interface.

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
+ imported and bounded evidence
+ operator-supplied backup-awareness metadata
→ source validation and provenance
→ deterministic cross-source findings
→ timeline and missing-evidence guidance
→ explicit operator hypotheses and root-cause assessment
→ current local JSON and Markdown outputs
→ immutable SQLite bundle, analysis and assessment revisions
→ API, CLI and operator workbench visibility
```

Current deterministic findings include:

- successful DNS resolution with failed HTTP reachability;
- contradictory availability evidence;
- forward/reverse DNS consistency requiring review;
- TLS certificate expiry risk;
- missing evidence for required dependencies.

OPSCORE never generates hypotheses or promotes root-cause status automatically. A confirmed operator assessment requires an explicit statement, supporting evidence and no unresolved required-evidence entries. These checks validate the record; they do not independently prove the conclusion.

## Quick start

```powershell
.\OPSCORE.ps1 setup
.\OPSCORE.ps1 verify
.\OPSCORE.ps1 demo
.\OPSCORE.ps1 correlate
.\OPSCORE.ps1 ui
.\OPSCORE.ps1 export
```

`OPSCORE.ps1 ui` opens the local operator workbench at `http://127.0.0.1:8000`.

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
python -m opscore.cli history inc-orders-001 `
  --workspace .opscore-data\api
python -m uvicorn opscore.api:app --host 127.0.0.1 --port 8000
```

Use `--revision 1` with the history command to retrieve one complete immutable revision payload.

## Bounded evidence collection

M4 collects read-only DNS, HTTP and TLS evidence for one explicit URL. M6 adds one explicit TCP-connectivity attempt for one host and port. OPSCORE does not crawl, scan ranges, enumerate neighboring hosts, retain response bodies or modify remote systems.

## Backup awareness

M7 records structured operator-supplied backup-awareness metadata for one existing incident service. OPSCORE does not connect to backup platforms, control jobs, change schedules or retention, perform restores, or infer recoverability.

## Immutable incident history

M8 introduced `incident-history.sqlite3` inside the configured workspace. M9 safely extends that history to include assessment revisions while preserving existing M8 bundle and analysis data.

OPSCORE records:

- one immutable bundle revision whenever a validated incident bundle is created or changed;
- one immutable analysis revision whenever analysis is explicitly run;
- one immutable assessment revision whenever an operator assessment is accepted;
- deterministic per-incident revision numbers;
- timezone-aware UTC timestamps;
- the complete validated JSON payload for every revision.

Current JSON and Markdown files remain available. History listing and retrieval are read-only. OPSCORE provides no restore, rollback, edit or delete controls for historical revisions.

## Investigation assessment

M9 separates deterministic findings from operator judgment.

Each hypothesis can record:

- a stable identifier and statement;
- open, supported, weakened, disproven or confirmed status;
- supporting and contradicting finding/evidence references;
- required evidence;
- operator rationale.

The root-cause assessment can remain unassessed, suspected, supported, confirmed or disproven. Every assessment records the operator identity and a timezone-aware assessment timestamp. Unknown or cross-incident references are rejected.

The API provides:

```text
GET /api/incidents/{incident_id}/assessment
PUT /api/incidents/{incident_id}/assessment
```

An analysis must exist before an assessment can be saved. OPSCORE does not generate or promote any assessment automatically.

## Operator workbench

The local interface provides validated incident intake, incident selection, service and dependency views, evidence inventory, immutable history, deterministic analysis, timelines, findings, missing evidence, safe checks and Markdown report preview. Operator assessment visibility is part of the M9 interface completion work.

User-controlled values are escaped before HTML rendering. The interface writes only to the configured local OPSCORE workspace.

## Developer workflow

From the repository root, verify a pull-request branch with:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\github-workflow.ps1 `
  verify-pr agent/example-branch
```

The script performs a normal authenticated push, waits for pull-request CI, prints Linux and Windows job results and saves failed logs to the current user's Downloads folder.

## Automated proof

The repository is configured to run on Linux and Windows:

- Ruff linting;
- strict mypy checks;
- pytest with an enforced 85% coverage minimum;
- deterministic demo generation;
- imported evidence correlation;
- bounded collector and connectivity safety tests;
- backup-awareness contract tests;
- SQLite history migration, persistence and immutability tests;
- investigation-assessment contract and API lifecycle tests;
- PowerShell operator verification;
- Playwright browser workflow with a screenshot artifact;
- review artifact generation.

## Safety boundary

OPSCORE is read-only first. It does not modify DNS, certificates, services, backup platforms, remote systems or production infrastructure. It does not generate hypotheses, infer root cause, remediate incidents, or restore, roll back, rewrite or delete incident-history revisions. Public repository data must remain synthetic or sanitized.

See `docs/safety-boundaries.md` for the full boundary.
