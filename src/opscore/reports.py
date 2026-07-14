from __future__ import annotations

import json

from opscore.models import IncidentAnalysis


def render_markdown(analysis: IncidentAnalysis) -> str:
    incident = analysis.incident
    lines = [
        "# OPSCORE Incident Evidence Report",
        "",
        (
            "> Findings reflect the evidence available to this investigation. They do not "
            "confirm root cause unless explicitly marked as confirmed and linked to "
            "sufficient supporting evidence."
        ),
        "",
        "## Executive summary",
        "",
        f"- Incident: `{incident.incident_id}` — **{incident.title}**",
        f"- Environment: `{incident.environment}`",
        f"- Severity: **{incident.severity.value}**",
        f"- Status: **{incident.status.value}**",
        f"- Root-cause status: **{incident.root_cause_status.value}**",
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
    lines.extend(["", "## Evidence findings", ""])
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
    lines.extend(
        [
            "## Limitations",
            "",
            "- M2 uses sanitized local and imported evidence only.",
            "- No external systems were queried or modified.",
            (
                "- Findings are deterministic evidence statements, not automatic "
                "root-cause declarations."
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