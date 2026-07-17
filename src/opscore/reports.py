from __future__ import annotations

import json

from opscore.assessment import InvestigationAssessment
from opscore.models import IncidentAnalysis


def render_markdown(
    analysis: IncidentAnalysis,
    assessment: InvestigationAssessment | None = None,
) -> str:
    incident = analysis.incident
    lines = [
        "# OPSCORE Incident Evidence Report",
        "",
        (
            "> Findings reflect the evidence available to this investigation. "
            "Operator assessments are recorded separately and are never generated "
            "or promoted automatically."
        ),
        "",
        "## Executive summary",
        "",
        f"- Incident: `{incident.incident_id}` — **{incident.title}**",
        f"- Environment: `{incident.environment}`",
        f"- Severity: **{incident.severity.value}**",
        f"- Status: **{incident.status.value}**",
        "",
        "## Reported symptom",
        "",
        incident.reported_symptom,
        "",
        "## Affected services",
        "",
    ]
    service_by_id = {service.service_id: service for service in analysis.services}
    for service_id in incident.affected_service_ids:
        service = service_by_id[service_id]
        lines.append(f"- `{service.service_id}` — {service.name} ({service.service_type})")
    lines.extend(["", "## Declared dependencies", ""])
    if analysis.dependencies:
        for dependency in analysis.dependencies:
            requirement = "required" if dependency.required else "optional"
            lines.append(
                f"- `{dependency.source_service_id}` {dependency.dependency_type} "
                f"`{dependency.target_service_id}` ({requirement})"
            )
    else:
        lines.append("- No dependencies declared.")
    lines.extend(["", "## Evidence inventory", ""])
    for item in analysis.evidence:
        lines.append(
            f"- `{item.evidence_id}` — {item.evidence_type} — {item.source_system} — "
            f"{item.collected_at.isoformat()}"
        )
    lines.extend(["", "## Timeline", ""])
    for event in analysis.timeline:
        lines.append(
            f"- {event.timestamp.isoformat()} — **{event.event_type}** — "
            f"{event.summary}"
        )
    lines.extend(["", "## Deterministic evidence findings", ""])
    if not analysis.findings:
        lines.append("- No deterministic findings were generated from the available evidence.")
    for finding in analysis.findings:
        lines.extend(
            [
                f"### {finding.code}",
                "",
                f"- Severity: **{finding.severity.value}**",
                f"- Confidence: **{finding.confidence.value}**",
                f"- Statement: {finding.statement}",
                (
                    "- Supporting evidence: "
                    f"{', '.join(finding.supporting_evidence_ids) or 'none'}"
                ),
                (
                    "- Contradictory evidence: "
                    f"{', '.join(finding.contradictory_evidence_ids) or 'none'}"
                ),
            ]
        )
        if finding.missing_evidence:
            lines.append(f"- Missing evidence: {', '.join(finding.missing_evidence)}")
        if finding.safe_next_checks:
            lines.append(f"- Safe next checks: {'; '.join(finding.safe_next_checks)}")
        if finding.non_actions:
            lines.append(f"- Non-actions: {'; '.join(finding.non_actions)}")
        lines.append("")

    lines.extend(["## Operator investigation assessment", ""])
    if assessment is None:
        lines.append("- No operator assessment has been recorded.")
    else:
        lines.extend(
            [
                f"- Assessed at: {assessment.assessed_at.isoformat()}",
                f"- Assessed by: {assessment.assessed_by}",
                f"- Root-cause status: **{assessment.root_cause.status.value}**",
                (
                    "- Root-cause statement: "
                    f"{assessment.root_cause.statement or 'not stated'}"
                ),
                f"- Operator rationale: {assessment.root_cause.operator_rationale}",
            ]
        )
        if assessment.root_cause.supporting_evidence_ids:
            lines.append(
                "- Supporting evidence: "
                + ", ".join(assessment.root_cause.supporting_evidence_ids)
            )
        if assessment.root_cause.unresolved_required_evidence:
            lines.append(
                "- Unresolved required evidence: "
                + ", ".join(assessment.root_cause.unresolved_required_evidence)
            )
        if assessment.root_cause.limitations:
            lines.append(
                "- Assessment limitations: "
                + "; ".join(assessment.root_cause.limitations)
            )
        lines.extend(["", "### Hypotheses", ""])
        if not assessment.hypotheses:
            lines.append("- No hypotheses recorded.")
        for hypothesis in assessment.hypotheses:
            lines.extend(
                [
                    f"- `{hypothesis.hypothesis_id}` — **{hypothesis.status.value}** — "
                    f"{hypothesis.statement}",
                    f"  - Rationale: {hypothesis.operator_rationale}",
                ]
            )

    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- OPSCORE uses sanitized local and imported evidence only.",
            "- No external systems were modified.",
            (
                "- Findings are deterministic evidence statements; operator "
                "assessment is explicit and separately identified."
            ),
            "",
            "## Evidence provenance",
            "",
            f"- Generated at: {analysis.generated_at.isoformat()}",
            f"- Evidence items: {len(analysis.evidence)}",
            f"- Findings: {len(analysis.findings)}",
            "",
        ]
    )
    return "\n".join(lines)


def render_json(analysis: IncidentAnalysis) -> str:
    return json.dumps(analysis.model_dump(mode="json"), indent=2, sort_keys=True)
