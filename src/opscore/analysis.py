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


def _nearby(left: EvidenceItem, right: EvidenceItem) -> bool:
    return (
        left.target_reference == right.target_reference
        and abs((left.collected_at - right.collected_at).total_seconds()) <= 300
    )


def _same_collection_context(left: EvidenceItem, right: EvidenceItem) -> bool:
    if not _nearby(left, right) or left.source_system != right.source_system:
        return False
    for key in ("source_location", "target_id", "requested_url"):
        a = left.normalized_data.get(key)
        b = right.normalized_data.get(key)
        if a is not None and b is not None and a != b:
            return False
    if left.raw_reference and right.raw_reference:
        return left.raw_reference == right.raw_reference
    return True


def _http_dns_findings(evidence: list[EvidenceItem]) -> list[Finding]:
    dns = [
        item for item in evidence
        if item.evidence_type == "dns-resolution"
        and item.normalized_data.get("resolved_ips")
    ]
    http = [item for item in evidence if item.evidence_type == "http-response"]
    failures = [
        item for item in http
        if item.normalized_data.get("status") is None
        and item.normalized_data.get("error")
    ]
    successes = [
        item for item in http
        if isinstance(item.normalized_data.get("status"), int)
        and 200 <= item.normalized_data["status"] < 300
    ]
    server_errors = [
        item for item in http
        if isinstance(item.normalized_data.get("status"), int)
        and 500 <= item.normalized_data["status"] <= 599
    ]
    findings: list[Finding] = []
    for failure in failures:
        matches = [item for item in dns if _same_collection_context(item, failure)]
        if matches:
            findings.append(
                _finding(
                    "DNS_OK_HTTP_UNAVAILABLE",
                    "Name resolution completed, but HTTP reachability was not established.",
                    FindingSeverity.CRITICAL,
                    Confidence.MEDIUM,
                    [matches[0].evidence_id, failure.evidence_id],
                    missing=["verified endpoint and collection context", "server-side logs"],
                    checks=["Compare source location, service port and collection time."],
                    non_actions=["Do not modify DNS solely from this finding."],
                )
            )
    for error in server_errors:
        findings.append(
            _finding(
                "HTTP_SERVER_ERROR",
                "An HTTP server error was observed; a response was received.",
                FindingSeverity.WARNING,
                Confidence.HIGH,
                [error.evidence_id],
                checks=["Inspect application and upstream dependency logs."],
                non_actions=["Do not infer a transport failure or confirmed root cause."],
            )
        )
    for failure in [*failures, *server_errors]:
        matches = [item for item in successes if _nearby(item, failure)]
        if matches:
            findings.append(
                _finding(
                    "CONTRADICTORY_AVAILABILITY_EVIDENCE",
                    "Availability evidence differs across nearby collection results.",
                    FindingSeverity.WARNING,
                    Confidence.MEDIUM,
                    [matches[0].evidence_id],
                    contradictory=[failure.evidence_id],
                    missing=["source location", "target instance identity"],
                    checks=["Compare collection times, endpoints and source locations."],
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
                    f"{provider} evidence reports high CPU in the imported snapshot.",
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
    # Preserve existing identifiers for unique codes; disambiguate repeated findings.
    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.finding_id] = counts.get(finding.finding_id, 0) + 1
    for finding in findings:
        if counts[finding.finding_id] > 1:
            suffix = "-".join(sorted(finding.supporting_evidence_ids))
            if suffix:
                finding.finding_id = f"{finding.finding_id}-{suffix}"
    return IncidentAnalysis(
        incident=bundle.incident,
        services=bundle.services,
        dependencies=bundle.dependencies,
        evidence=bundle.evidence,
        timeline=_build_timeline(bundle),
        findings=findings,
        generated_at=generated_at or datetime.now(UTC),
    )