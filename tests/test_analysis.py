from pathlib import Path

from opscore.analysis import analyze
from opscore.demo import load_bundle

SAMPLE = Path("samples/incidents/orders-service-unavailable.json")


def test_sample_generates_expected_findings() -> None:
    analysis = analyze(load_bundle(SAMPLE))
    codes = {finding.code for finding in analysis.findings}
    assert codes == {
        "DNS_OK_HTTP_UNAVAILABLE",
        "CONTRADICTORY_AVAILABILITY_EVIDENCE",
        "DNS_FORWARD_REVERSE_REVIEW_REQUIRED",
        "TLS_CERTIFICATE_EXPIRY_RISK",
        "REQUIRED_DEPENDENCY_EVIDENCE_MISSING",
    }


def test_timeline_is_chronological() -> None:
    analysis = analyze(load_bundle(SAMPLE))
    timestamps = [event.timestamp for event in analysis.timeline]
    assert timestamps == sorted(timestamps)


def test_findings_do_not_confirm_root_cause() -> None:
    analysis = analyze(load_bundle(SAMPLE))
    assert analysis.incident.root_cause_status.value == "unassessed"
    assert all("caused" not in finding.statement.lower() for finding in analysis.findings)
