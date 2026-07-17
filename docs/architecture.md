# OPSCORE architecture

## Product boundary

OPSCORE is an incident investigation and evidence-correlation workbench for infrastructure and production operations.

It does not schedule recurring checks or manage monitoring actions; that belongs to WATCH. It does not replace DNS Audit Tool, which remains a specialist evidence provider.

## Data flow

```text
incident context
+ service and dependency definitions
+ imported or bounded collected evidence
→ validated domain models
→ deterministic correlation rules
→ chronological timeline
→ findings, contradictions and missing evidence
→ current JSON and Markdown outputs
→ immutable SQLite bundle and analysis revisions
```

## Layers

- `models.py`: incident, service, dependency, evidence, finding and timeline contracts.
- `adapters/`: source-specific normalization with provenance.
- `analysis.py`: deterministic cross-source correlation.
- `reports.py`: support-ready Markdown and JSON output.
- `history.py`: append-only SQLite revision metadata and payload storage.
- `storage.py`: compatibility layer for current JSON/report files plus immutable history recording.
- `demo.py` and `imports.py`: vertical workflow orchestration.
- `cli.py`, `api.py` and `ui.py`: operator interfaces.

Collectors must not persist state, render reports or declare root cause. Correlation rules must reference evidence and expose limitations.

## Storage

OPSCORE keeps two complementary local storage views inside one startup-configured workspace:

1. **Current-state compatibility files**
   - one current incident bundle JSON per incident;
   - one current analysis JSON per incident;
   - one current Markdown report per incident.

2. **Immutable incident history**
   - one local SQLite database named `incident-history.sqlite3`;
   - ordered per-incident bundle and analysis revisions;
   - complete validated JSON payloads;
   - timezone-aware UTC creation timestamps;
   - read-only listing and retrieval through service, API, CLI and operator UI surfaces.

History bootstrap creates the database schema automatically without rewriting existing incident JSON. Historical revisions are append-only: OPSCORE exposes no restore, rollback, edit or delete operation.
