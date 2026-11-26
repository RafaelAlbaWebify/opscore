from datetime import timedelta
from pathlib import Path

from opscore.analysis import analyze
from opscore.demo import load_bundle
from opscore.models import EvidenceItem

SAMPLE = Path("samples/incidents/orders-service-unavailable.json")


def test_unrelated_dns_not_correlated() -> None:
    bundle = load_bundle(SAMPLE)
    dns, failure = bundle.evidence[:2]
    failure = failure.model_copy(update={"target_reference": "identity"})
    bundle.evidence = [dns, failure]
    assert "DNS_OK_HTTP_UNAVAILABLE" not in {f.code for f in analyze(bundle).findings}


def test_distant_observations_not_correlated() -> None:
    bundle = load_bundle(SAMPLE)
    dns, failure = bundle.evidence[:2]
    failure = failure.model_copy(update={"collected_at": dns.collected_at + timedelta(hours=1)})
    bundle.evidence = [dns, failure]
    assert "DNS_OK_HTTP_UNAVAILABLE" not in {f.code for f in analyze(bundle).findings}


def test_503_is_server_response_not_transport_failure() -> None:
    bundle = load_bundle(SAMPLE)
    dns, failure = bundle.evidence[:2]
    failure = failure.model_copy(update={"normalized_data": {"status": 503}})
    bundle.evidence = [dns, failure]
    codes = {f.code for f in analyze(bundle).findings}
    assert "HTTP_SERVER_ERROR" in codes
    assert "DNS_OK_HTTP_UNAVAILABLE" not in codes


def test_multiple_cloud_findings_have_distinct_ids() -> None:
    bundle = load_bundle(SAMPLE)
    bundle.evidence = [
        EvidenceItem(
            evidence_id=f"ev-cloud-{i}",
            evidence_type="cloud-vm-state",
            source_system="synthetic",
            collected_at=bundle.incident.reported_at,
            target_reference="orders-web",
            normalized_data={"provider": "azure", "cpu_percent": 90},
        )
        for i in range(2)
    ]
    findings = [f for f in analyze(bundle).findings if f.code == "AZURE_HIGH_CPU"]
    assert len(findings) == 2
    assert len({f.finding_id for f in findings}) == 2
    assert all("sustained" not in f.statement for f in findings)
