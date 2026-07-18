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
→ explicit operator hypotheses and root-cause assessment
→ current JSON and Markdown outputs
→ immutable SQLite bundle, analysis and assessment revisions
```

Deterministic analysis and operator assessment are separate layers. `analysis.py` never generates hypotheses or promotes root-cause status.

## Layers

- `models.py`: incident, service, dependency, evidence, finding and timeline contracts.
- `assessment.py`: operator-controlled hypothesis/root-cause contracts and reference validation.
- `adapters/`: source-specific normalization with provenance.
- `analysis.py`: deterministic cross-source correlation.
- `reports.py`: support-ready output with separate deterministic and operator sections.
- `history.py`: append-only SQLite revision metadata and payload storage.
- `storage.py`: current JSON/report files plus immutable revision recording.
- `demo.py` and `imports.py`: vertical workflow orchestration.
- `cli.py` and `api.py`: command-line and HTTP operator interfaces.
- `ui.py`: base server-rendered operator-interface HTML and core interaction script.
- `assessment_ui.py`: interface composition entry point that adds assessment visibility and applies the presentation pipeline.
- `visual_refresh.py` and `operational_ui.py`: TRACE-aligned visual shell, operational summary, incident register and main-workspace intake.
- `layout_finish.py`: full-page and responsive layout stabilization.
- `ux_polish.py` and `ux_compatibility.py`: progressive disclosure, task navigation, accessible feedback and compatibility-preserving interaction enhancements.
- `professional_finish.py`: final report formatting, responsive presentation and verified interaction-state fixes.

The FastAPI root route renders the base interface from `ui.py` and passes it through `assessment_ui.enhance_operator_interface()`, which applies the presentation modules in a fixed order. These modules enhance presentation and interaction while preserving the incident-domain and API behavior.

Collectors must not persist state, render reports or declare root cause. Correlation rules must reference evidence and expose limitations. Assessment status changes require explicit operator input.

## Storage

OPSCORE keeps two complementary local storage views inside one startup-configured workspace:

1. **Current-state compatibility files**
   - one current incident bundle JSON per incident;
   - one current analysis JSON per incident;
   - one current assessment JSON per incident;
   - one current Markdown report per incident.

2. **Immutable incident history**
   - one local SQLite database named `incident-history.sqlite3`;
   - ordered per-incident bundle, analysis and assessment revisions;
   - complete validated JSON payloads;
   - timezone-aware UTC creation timestamps;
   - read-only listing and retrieval.

M9 safely migrates an existing M8 history table to allow assessment revisions, copies existing bundle/analysis rows unchanged and then removes the temporary M8 table. Historical revisions remain append-only: OPSCORE exposes no restore, rollback, edit or delete operation.
