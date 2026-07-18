# OPSCORE

[![OPSCORE CI](https://github.com/RafaelAlbaWebify/opscore/actions/workflows/ci.yml/badge.svg)](https://github.com/RafaelAlbaWebify/opscore/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![Version](https://img.shields.io/badge/version-0.9.0-135fca)
![License](https://img.shields.io/badge/license-MIT-287a4a)

> Local-first incident evidence and investigation workbench for infrastructure and production operations.

OPSCORE helps an operator turn scattered technical evidence into a structured, reviewable incident record. It combines service context, imported and bounded live evidence, deterministic findings, immutable history and explicit operator assessment through a CLI, API, Markdown reports and a professional local browser interface.

**Status:** completed portfolio MVP · **Version:** `0.9.0` · **Operation:** local-first and read-only by design

## Why OPSCORE exists

Infrastructure incidents rarely fail because a single command is unavailable. They fail because evidence is fragmented across DNS checks, endpoint tests, service dependencies, backup context, timelines and human assumptions.

OPSCORE provides one controlled workspace for:

- preserving incident and service context;
- importing sanitized DNS Audit Tool CSV and WATCH v1 handoffs;
- running bounded single-target DNS, HTTP, TLS and TCP-connectivity checks;
- validating evidence provenance;
- producing deterministic cross-source findings;
- identifying missing evidence and safe next checks;
- recording explicit hypotheses and root-cause assessment;
- preserving immutable bundle, analysis and assessment revisions;
- generating a reviewable incident report.

## Operator workflow

```text
Create or import incident context
            ↓
Collect bounded read-only evidence
            ↓
Validate provenance and correlate findings
            ↓
Review timeline, missing evidence and safe checks
            ↓
Record evidence-backed operator assessment
            ↓
Preserve immutable revisions and export report
```

OPSCORE never generates hypotheses or promotes root-cause status automatically. A confirmed assessment requires an explicit conclusion, supporting evidence and no unresolved required-evidence entries.

## Main capabilities

### Incident evidence workbench

- Validated incident, service and dependency models.
- Evidence inventory with source, timestamp and provenance.
- Timeline, findings, missing-evidence guidance and safe-check suggestions.
- Current JSON and Markdown outputs for local review.

### Bounded evidence collection

- One explicit URL for DNS, HTTP and TLS collection.
- One explicit host and port for TCP-connectivity evidence.
- No network-range scanning, crawling, neighboring-host discovery or response-body retention.

### Evidence correlation

Current deterministic rules include:

- successful DNS resolution with failed HTTP reachability;
- contradictory availability evidence;
- forward/reverse DNS consistency requiring review;
- TLS certificate expiry risk;
- missing evidence for required dependencies.

### Immutable history

The local SQLite history database records:

- bundle revisions when validated incident evidence changes;
- analysis revisions when deterministic analysis is explicitly run;
- assessment revisions when an operator assessment is accepted;
- deterministic revision numbers and timezone-aware UTC timestamps;
- the complete validated JSON payload for every revision.

History is read-only. OPSCORE provides no revision edit, delete, restore or rollback controls.

### Investigation assessment

Operators can maintain hypotheses with:

- stable identifiers and statements;
- open, supported, weakened, disproven or confirmed status;
- supporting and contradicting references;
- required evidence;
- rationale and operator identity.

Root-cause status can remain unassessed, suspected, supported, confirmed or disproven. Unknown and cross-incident references are rejected.

### Professional operator interface

The local browser workbench includes:

- operational KPI summary and searchable incident register;
- collapsed validated incident intake;
- task-oriented investigation navigation;
- progressive disclosure for evidence, history and reports;
- accessible loading, success, empty and error states;
- human-readable timestamps;
- safely formatted report presentation;
- synchronized operator assessment;
- desktop and narrow-screen layouts.

## Quick start on Windows

From PowerShell in the repository root:

```powershell
.\OPSCORE.ps1 setup
.\OPSCORE.ps1 verify
.\OPSCORE.ps1 demo
.\OPSCORE.ps1 correlate
.\OPSCORE.ps1 ui
```

The workbench opens at:

```text
http://127.0.0.1:8000
```

Create a review package with:

```powershell
.\OPSCORE.ps1 export
```

## Direct Python usage

```powershell
python -m pip install -e ".[dev,browser]"
python -m opscore.cli demo --workspace .opscore-data
python -m opscore.cli correlate --workspace .opscore-data\imported
python -m uvicorn opscore.api:app --host 127.0.0.1 --port 8000
```

Selected evidence commands:

```powershell
python -m opscore.cli collect --url https://example.test/health `
  --target-reference service-web --source-location operator-laptop

python -m opscore.cli connectivity --host example.test --port 443 `
  --target-reference service-web --source-location operator-laptop

python -m opscore.cli watch-handoff `
  --handoff-file samples/imports/watch-handoff-v1.json

python -m opscore.cli history inc-orders-001 `
  --workspace .opscore-data\api
```

Use `--revision 1` with `history` to retrieve one complete immutable revision payload.

## API surface

The FastAPI service exposes bounded incident, analysis, history, report and assessment operations. Assessment endpoints include:

```text
GET /api/incidents/{incident_id}/assessment
PUT /api/incidents/{incident_id}/assessment
```

An analysis must exist before an assessment can be saved. OpenAPI contract tests protect the public API surface.

## Automated verification

Every pull request is tested on Linux and Windows.

Linux verification includes:

- Ruff linting;
- strict mypy checks;
- pytest with an enforced 85% coverage minimum;
- deterministic demo and import-correlation workflows;
- FastAPI startup;
- Playwright desktop and 390-pixel browser journeys;
- screenshot and proof-artifact generation.

Windows verification includes:

- package installation on a clean GitHub-hosted Windows runner;
- Ruff, strict mypy and pytest through `OPSCORE.ps1 verify`;
- demo and import-correlation workflows;
- review-package export and proof collection.

This is evidence for the tested environments and documented workflows. It is not a claim of compatibility with every Windows configuration, security policy or manual user sequence.

## Safety boundary

OPSCORE is read-only first. It does not:

- modify DNS, certificates, services or remote systems;
- scan networks or enumerate neighboring hosts;
- control backup jobs, retention or restores;
- generate hypotheses or infer root cause;
- remediate incidents;
- rewrite or delete immutable history.

Public repository data must remain synthetic or sanitized. See [`docs/safety-boundaries.md`](docs/safety-boundaries.md).

## Architecture and documentation

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/api.md`](docs/api.md)
- [`docs/incident-history.md`](docs/incident-history.md)
- [`docs/investigation-assessment.md`](docs/investigation-assessment.md)
- [`docs/roadmap.md`](docs/roadmap.md)
- [`docs/safety-boundaries.md`](docs/safety-boundaries.md)
- [`docs/releases/v0.9.0.md`](docs/releases/v0.9.0.md)

## Portfolio context

OPSCORE is Rafael Alba's flagship project for the **Infrastructure / Production Operations Engineer** path.

It is deliberately separated from:

- **WATCH** — recurring public-safe operational website checks;
- **TRACE** — IAM and access-evidence workflows;
- **CustosOps** — defensive security evidence;
- **DNS Audit Tool** — specialist evidence provider used by OPSCORE.

## License

MIT License. See [`LICENSE`](LICENSE).