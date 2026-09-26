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
                summary=(
                    f"{item.evidence_type} evidence collected for "
                    f"{item.target_reference}"
                ),
                evidence_id=item.evidence_id,
            )
        )
    return sorted(events, key=lambda event: (event.timestamp, event.event_id))


def _http_dns_findings(evidence: list[EvidenceItem]) -> list[Finding]:
    dns_success = [
        item
        for item in evidence
        if item.evidence_type == "dns-resolution"
        and item.normalized_data.get("resolved_ips")
    ]
    http_fail = [
        item
        for item in evidence
        if item.evidence_type == "http-response"
        and (
            item.normalized_data.get("status") is None
            or item.normalized_data.get("error")
        )
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
                (
                    "Name resolution completed, but application-layer "
                    "reachability was not established."
                ),
                FindingSeverity.CRITICAL,
                Confidence.HIGH,
                [dns_success[0].evidence_id, http_fail[0].evidence_id],
                missing=[
                    "port/connectivity path",
                    "server-side service state",
                    "application logs",
                ],
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
                missing=[
                    "source location",
                    "resolved address per run",
                    "target instance identity",
                ],
                checks=[
                    (
                        "Compare collection times, source locations, DNS answers "
                        "and target instances."
                    )
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
            missing=[
                "confirmation that reverse DNS is required by the affected workflow"
            ],
            checks=["Validate record ownership and expected forward/reverse naming."],
            non_actions=[
                "Do not delete or modify DNS records without ownership validation."
            ],
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
            (
                "The available certificate evidence is within the configured "
                "30-day expiry window."
            ),
            FindingSeverity.WARNING,
            Confidence.HIGH,
            [item.evidence_id for item in expiring],
            missing=["certificate renewal ownership", "deployment path"],
            checks=[
                "Confirm renewal ownership and the certificate deployment procedure."
            ],
            non_actions=[
                "Do not claim the certificate caused the incident without handshake evidence."
            ],
        )
    ]



def _cloud_findings(evidence: list[EvidenceItem]) -> list[Finding]:
    findings: list[Finding] = []
    for item in evidence:
        if item.evidence_type not in {"cloud-vm-state", "cloud-instance-state"}:
            continue
        provider = str(item.normalized_data.get("provider", "cloud")).upper()
        network = str(item.normalized_data.get("network_reachability", "")).lower()
        health = str(item.normalized_data.get("resource_health", "")).lower()
        status_check = str(item.normalized_data.get("status_check", "")).lower()
        cpu = item.normalized_data.get("cpu_percent")
        disk = item.normalized_data.get("disk_free_percent")

        if network in {"failed", "unreachable", "false"}:
            findings.append(
                _finding(
                    f"{provider}_NETWORK_REVIEW_REQUIRED",
                    f"{provider} evidence reports failed network reachability.",
                    FindingSeverity.CRITICAL,
                    Confidence.HIGH,
                    [item.evidence_id],
                    missing=["effective network-policy and route context", "DNS context"],
                    checks=[
                        "Review effective network controls, routes and DNS before recovery action."
                    ],
                    non_actions=[
                        "Do not restart or reconfigure the resource solely from "
                        "reachability evidence."
                    ],
                )
            )
        if health and health not in {"available", "unknown", "none"}:
            findings.append(
                _finding(
                    "AZURE_RESOURCE_HEALTH_REVIEW_REQUIRED",
                    "Azure Resource Health evidence is not Available.",
                    FindingSeverity.CRITICAL,
                    Confidence.HIGH,
                    [item.evidence_id],
                    checks=["Review Resource Health details and platform-event context."],
                )
            )
        if status_check and status_check not in {"ok", "passed", "unknown", "none"}:
            findings.append(
                _finding(
                    "AWS_STATUS_CHECK_REVIEW_REQUIRED",
                    "AWS status-check evidence is not healthy.",
                    FindingSeverity.CRITICAL,
                    Confidence.HIGH,
                    [item.evidence_id],
                    checks=[
                        "Separate system-status and instance-status evidence before "
                        "recovery action."
                    ],
                )
            )
        if isinstance(cpu, (int, float)) and cpu >= 85:
            findings.append(
                _finding(
                    f"{provider}_HIGH_CPU",
                    f"{provider} evidence reports sustained high CPU in the imported snapshot.",
                    FindingSeverity.WARNING,
                    Confidence.MEDIUM,
                    [item.evidence_id],
                    checks=["Correlate resource pressure with workload and timeline evidence."],
                )
            )
        if isinstance(disk, (int, float)) and disk <= 10:
            findings.append(
                _finding(
                    f"{provider}_LOW_DISK",
                    f"{provider} evidence reports low free disk capacity.",
                    FindingSeverity.CRITICAL,
                    Confidence.HIGH,
                    [item.evidence_id],
                    checks=[
                        "Validate filesystem usage and growth before resizing or deleting data."
                    ],
                    non_actions=["Do not delete data solely from this finding."],
                )
            )
    return findings


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
            (
                "The investigation contains no direct evidence for required "
                f"dependencies: {names}."
            ),
            FindingSeverity.WARNING,
            Confidence.HIGH,
            [],
            missing=[
                f"dependency evidence for {dep.target_service_id}"
                for dep in missing_dependencies
            ],
            checks=[
                (
                    "Collect bounded evidence for each required dependency "
                    "before concluding root cause."
                )
            ],
        )
    ]


def analyze(
    bundle: IncidentBundle,
    generated_at: datetime | None = None,
) -> IncidentAnalysis:
    findings = []
    findings.extend(_http_dns_findings(bundle.evidence))
    findings.extend(_dns_audit_findings(bundle.evidence))
    findings.extend(_tls_findings(bundle.evidence))
    findings.extend(_cloud_findings(bundle.evidence))
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