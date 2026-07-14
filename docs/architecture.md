# OPSCORE architecture

## Product boundary

OPSCORE is an incident investigation and evidence-correlation workbench for infrastructure and production operations.

It does not schedule recurring checks or manage monitoring actions; that belongs to WATCH. It does not replace DNS Audit Tool, which remains a specialist evidence provider.

## Data flow

```text
incident context
+ service and dependency definitions
+ imported evidence adapters
→ validated domain models
→ deterministic correlation rules
→ chronological timeline
→ findings, contradictions and missing evidence
→ Markdown and JSON reports
```

## Layers

- `models.py`: incident, service, dependency, evidence, finding and timeline contracts.
- `adapters/`: source-specific normalization with provenance.
- `analysis.py`: deterministic cross-source correlation.
- `reports.py`: support-ready Markdown and JSON output.
- `demo.py` and `imports.py`: vertical workflow orchestration.
- `cli.py` and `api.py`: operator interfaces.

Collectors must not persist state, render reports or declare root cause. Correlation rules must reference evidence and expose limitations.

## Storage

M1 writes deterministic local files only. Database persistence is deferred until incident history and search requirements justify it.
