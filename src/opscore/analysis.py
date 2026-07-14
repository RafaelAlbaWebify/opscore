from __future__ import annotations

from datetime import UTC, datetime

from opscore.models import (
    Confidence,
    EvidenceItem,
    Finding,
    FindingSeverity,
    IncidentAnalysis,
    IncidentBundle,
    TimelineEvent,
)


def _finding(
    code: str,
    statement: str,
    severity: FindingSeverity,
    confidence: Confidence,
    supporting: list[str],
    *,
    contradictory: list[str] | None = None,
    missing: list[str] | None = None,
    checks: list[str] | None = None,
    non_actions: list[str] | None = None,
) -> Finding:
    return Finding(
        finding_id=f"finding-{code.lower().replace('_', '-')}",
        code=code,
        statement=statement,
        severity=severity,
        confidence=confidence,
        supporting_evidence_ids=supporting,
        contradictory_evidence_ids=contradictory or [],
        missing_evidence=missing or [],
        safe_next_checks=checks or [],
        non_actions=non_actions or [],
    )


def _build_timeline(bundle: IncidentBundle) -> list[TimelineEvent]:
    events = [
        TimelineEvent(
            event_id="event-reported",
            timestamp=bundle.incident.reported_at,
            source="incident-intake",
            event_type="reported",
            summary=bundle.incident.reported_symptom,
        )
    ]
    for item in bundle.evidence:
        events.append(
            TimelineEvent(
                event_id=f"event-{item.evidence_id}",
                timestamp=item.collected_at,
                source=item.source_system,
                event_type=item.evidence_type,
                summary=f"{item.evidence_type} evidence collected for {item.target_reference}",
                evidence_id=item.evidence_id,
            )
        )
    return sorted(events, key=lambda event: (event.timestamp, event.event_id))


def _http_dns_findings(evidence: list[EvidenceItem]) -> list[Finding]:
    dns_success = [
        item
        for item in evidence
        if item.evidence_type == "dns-resolution" and item.normalized_data.get("resolved_ips")
    ]
    http_fail = [
        item
        for item in evidence
        if item.evidence_type == "http-response"
        and (item.normalized_data.get("status") is None or item.normalized_data.get("error"))
    ]
    http_success = [
        item
        for item in evidence
        if item.evidence_type == "http-response"
        and isinstance(item.normalized_data.get("status"), int)
        and 200 <= item.normalized_data["status"] < 400
    ]
    findings: list[Finding] = []
    if dns_success and http_fail:
        findings.append(
            _finding(
                "DNS_OK_HTTP_UNAVAILABLE",
                "Name resolution completed, but application-layer reachability was not established.",
                FindingSeverity.CRITICAL,
                Confidence.HIGH,
                [dns_success[0].evidence_id, http_fail[0].evidence_id],
                missing=["port/connectivity path", "server-side service state", "application logs"],
                checks=[
                    "Validate the configured service port from an approved source location.",
                    "Review service and application logs for the evidence time window.",
                ],
                non_actions=["Do not modify DNS solely from this finding."],
            )
        )
    if http_success and http_fail:
        findings.append(
            _finding(
                "CONTRADICTORY_AVAILABILITY_EVIDENCE",
                "Availability evidence is contradictory across collection results.",
                FindingSeverity.WARNING,
                Confidence.HIGH,
                [http_success[0].evidence_id],
                contradictory=[http_fail[0].evidence_id],
                missing=["source location", "resolved address per run", "target instance identity"],
                checks=[
                    "Compare collection times, source locations, DNS answers and target instances."
                ],
            )
        )
    return findings


def _dns_audit_findings(evidence: list[EvidenceItem]) -> list[Finding]:
    relevant = [
        item
        for item in evidence
        if item.evidence_type == "dns-audit-finding"
        and item.normalized_data.get("finding") in {"Missing PTR", "PTR mismatch"}
    ]
    if not relevant:
        return []
    return [
        _finding(
            "DNS_FORWARD_REVERSE_REVIEW_REQUIRED",
            "Forward/reverse DNS consistency requires validation.",
            FindingSeverity.WARNING,
            Confidence.MEDIUM,
            [item.evidence_id for item in relevant],
            missing=["confirmation that reverse DNS is required by the affected workflow"],
            checks=["Validate record ownership and expected forward/reverse naming."],
            non_actions=["Do not delete or modify DNS records without ownership validation."],
        )
    ]


def _tls_findings(evidence: list[EvidenceItem]) -> list[Finding]:
    expiring = [
        item
        for item in evidence
        if item.evidence_type == "tls-certificate"
        and isinstance(item.normalized_data.get("days_remaining"), int)
        and item.normalized_data["days_remaining"] < 30
    ]
    if not expiring:
        return []
    return [
        _finding(
            "TLS_CERTIFICATE_EXPIRY_RISK",
            "The available certificate evidence is within the configured 30-day expiry window.",
            FindingSeverity.WARNING,
            Confidence.HIGH,
            [item.evidence_id for item in expiring],
            missing=["certificate renewal ownership", "deployment path"],
            checks=["Confirm renewal ownership and the certificate deployment procedure."],
            non_actions=[
                "Do not claim the certificate caused the incident without handshake evidence."
            ],
        )
    ]


def _dependency_findings(bundle: IncidentBundle) -> list[Finding]:
    evidence_targets = {item.target_reference for item in bundle.evidence}
    missing_dependencies = [
        dependency
        for dependency in bundle.dependencies
        if dependency.required and dependency.target_service_id not in evidence_targets
    ]
    if not missing_dependencies:
        return []
    names = ", ".join(sorted(dep.target_service_id for dep in missing_dependencies))
    return [
        _finding(
            "REQUIRED_DEPENDENCY_EVIDENCE_MISSING",
            f"The investigation contains no direct evidence for required dependencies: {names}.",
            FindingSeverity.WARNING,
            Confidence.HIGH,
            [],
            missing=[
                f"dependency evidence for {dep.target_service_id}"
                for dep in missing_dependencies
            ],
            checks=[
                "Collect bounded evidence for each required dependency before concluding root cause."
            ],
        )
    ]


def analyze(bundle: IncidentBundle, generated_at: datetime | None = None) -> IncidentAnalysis:
    findings = []
    findings.extend(_http_dns_findings(bundle.evidence))
    findings.extend(_dns_audit_findings(bundle.evidence))
    findings.extend(_tls_findings(bundle.evidence))
    findings.extend(_dependency_findings(bundle))
    return IncidentAnalysis(
        incident=bundle.incident,
        services=bundle.services,
        dependencies=bundle.dependencies,
        evidence=bundle.evidence,
        timeline=_build_timeline(bundle),
        findings=findings,
        generated_at=generated_at or datetime.now(UTC),
    )
