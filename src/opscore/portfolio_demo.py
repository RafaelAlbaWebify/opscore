from __future__ import annotations

from datetime import datetime

from opscore.analysis import analyze
from opscore.assessment import (
    HypothesisAssessment,
    InvestigationAssessment,
    RootCauseAssessment,
)
from opscore.models import (
    Confidence,
    Dependency,
    EvidenceItem,
    HypothesisStatus,
    Incident,
    IncidentBundle,
    IncidentSeverity,
    IncidentStatus,
    RootCauseStatus,
    Service,
)
from opscore.storage import IncidentStore

DEMO_INCIDENT_ID = "inc-portfolio-ops-001"


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def build_portfolio_demo() -> IncidentBundle:
    """Build one deterministic, synthetic infrastructure-operations review case."""
    incident = Incident(
        incident_id=DEMO_INCIDENT_ID,
        title="Orders portal unreachable from one location",
        reported_symptom=(
            "Users at one source location cannot reach the orders portal while "
            "a second source reports HTTP 200."
        ),
        environment="production-like demo",
        reported_at=_dt("2026-09-26T08:55:00Z"),
        investigation_started_at=_dt("2026-09-26T09:00:00Z"),
        affected_service_ids=["orders-web"],
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.ANALYZING,
        root_cause_status=RootCauseStatus.SUPPORTED,
    )
    services = [
        Service(
            service_id="orders-web", name="Orders Web", environment="production-like demo",
                service_type="web", owner="Application Operations", criticality=IncidentSeverity.HIGH),
        Service(
            service_id="identity", name="Identity Service", environment="production-like demo",
                service_type="identity", owner="Identity Operations", criticality=IncidentSeverity.HIGH),
        Service(
            service_id="orders-db", name="Orders Database", environment="production-like demo",
                service_type="database", owner="Database Operations", criticality=IncidentSeverity.HIGH),
    ]
    dependencies = [
        Dependency(dependency_id="dep-orders-identity", source_service_id="orders-web",
                   target_service_id="identity", dependency_type="authenticates-through",
                   evidence_source="synthetic service map", confidence=Confidence.HIGH),
        Dependency(dependency_id="dep-orders-db", source_service_id="orders-web",
                   target_service_id="orders-db", dependency_type="reads-from",
                   evidence_source="synthetic service map", confidence=Confidence.HIGH),
    ]
    evidence = [
        EvidenceItem(
            evidence_id="ev-demo-dns", evidence_type="dns-resolution",
                     source_system="WATCH synthetic export", collected_at=_dt("2026-09-26T09:01:00Z"),
                     target_reference="orders-web",
                     normalized_data={"hostname": "orders.example.test", "resolved_ips": ["203.0.113.10"]},
                     limitations=["Documentation-only address."]),
        EvidenceItem(
            evidence_id="ev-demo-http-fail", evidence_type="http-response",
                     source_system="WATCH synthetic export", collected_at=_dt("2026-09-26T09:01:05Z"),
                     target_reference="orders-web",
                     normalized_data={"status": None, "error": "connection timeout",
                                      "source_location": "site-a"}),
        EvidenceItem(
            evidence_id="ev-demo-http-ok", evidence_type="http-response",
                     source_system="operator synthetic evidence", collected_at=_dt("2026-09-26T09:02:00Z"),
                     target_reference="orders-web",
                     normalized_data={"status": 200, "response_ms": 228,
                                      "source_location": "site-b"}),
        EvidenceItem(
            evidence_id="ev-demo-azure", evidence_type="cloud-vm-state",
                     source_system="azure-export", collected_at=_dt("2026-09-26T09:03:00Z"),
                     target_reference="orders-web",
                     normalized_data={"provider": "azure", "resource_name": "az-orders-01",
                                      "power_state": "running", "resource_health": "available",
                                      "network_reachability": "failed", "cpu_percent": 24,
                                      "disk_free_percent": 48},
                     raw_reference="synthetic-azure-vm-export.json",
                     limitations=["Imported synthetic export only; no live Azure tenant connection.",
                                  "Reachability evidence does not identify the failing network control."]),
        EvidenceItem(
            evidence_id="ev-demo-tls", evidence_type="tls-certificate",
                     source_system="WATCH synthetic export", collected_at=_dt("2026-09-26T09:04:00Z"),
                     target_reference="orders-web",
                     normalized_data={"days_remaining": 21, "hostname_match": True}),
    ]
    return IncidentBundle(
        incident=incident,
        services=services,
        dependencies=dependencies,
        evidence=evidence,
    )


def seed_portfolio_demo(store: IncidentStore) -> str:
    bundle = build_portfolio_demo()
    store.save_bundle(bundle)
    analysis = analyze(bundle, generated_at=_dt("2026-09-26T09:04:00Z"))
    store.save_analysis(analysis)
    assessment = InvestigationAssessment(
        incident_id=DEMO_INCIDENT_ID,
        assessed_at=_dt("2026-09-26T09:10:00Z"),
        assessed_by="Application / Infrastructure Operations",
        hypotheses=[
            HypothesisAssessment(
                hypothesis_id="hyp-demo-network-path",
                statement=(
                    "A source-location-specific network path or control may be contributing "
                    "to the reachability failure."
                ),
                status=HypothesisStatus.SUPPORTED,
                supporting_finding_ids=[
                    "finding-dns-ok-http-unavailable",
                    "finding-contradictory-availability-evidence",
                    "finding-azure-network-review-required",
                ],
                supporting_evidence_ids=[
                    "ev-demo-dns", "ev-demo-http-fail", "ev-demo-http-ok", "ev-demo-azure"
                ],
                required_evidence=[
                    "effective route and network-policy context for site-a",
                    "direct evidence for required identity and database dependencies",
                ],
                operator_rationale=(
                    "DNS succeeds, reachability differs by source location, and the imported "
                    "Azure snapshot also reports failed network reachability. These signals "
                    "narrow the investigation but do not identify a root cause."
                ),
            )
        ],
        root_cause=RootCauseAssessment(
            status=RootCauseStatus.SUPPORTED,
            statement="Network-path involvement is supported but not confirmed.",
            supporting_finding_ids=["finding-contradictory-availability-evidence"],
            supporting_evidence_ids=["ev-demo-http-fail", "ev-demo-http-ok"],
            unresolved_required_evidence=[
                "effective network controls and routes",
                "required dependency evidence",
            ],
            limitations=[
                "Azure evidence is an imported synthetic snapshot, not a live tenant query."
            ],
            operator_rationale=(
                "The evidence supports further network-path investigation. Root cause remains "
                "unconfirmed until route/control and dependency evidence is reviewed."
            ),
        ),
    )
    store.save_assessment(assessment)
    return DEMO_INCIDENT_ID
