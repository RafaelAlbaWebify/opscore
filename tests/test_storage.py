from datetime import UTC, datetime
from pathlib import Path

from opscore.analysis import analyze
from opscore.assessment import InvestigationAssessment, RootCauseAssessment
from opscore.demo import load_bundle
from opscore.storage import IncidentStore

SAMPLE = Path("samples/incidents/orders-service-unavailable.json")


def test_store_round_trip(tmp_path: Path) -> None:
    store = IncidentStore(tmp_path)
    bundle = load_bundle(SAMPLE)
    store.save_bundle(bundle)
    assert store.load_bundle(bundle.incident.incident_id) == bundle
    assert [item.incident.incident_id for item in store.list_bundles()] == [
        bundle.incident.incident_id
    ]


def test_store_analysis_and_report(tmp_path: Path) -> None:
    store = IncidentStore(tmp_path)
    analysis = analyze(load_bundle(SAMPLE))
    store.save_analysis(analysis)
    assert store.load_analysis(analysis.incident.incident_id) == analysis
    report = store.load_report(analysis.incident.incident_id)
    assert report is not None
    assert "# OPSCORE Incident Evidence Report" in report


def test_store_assessment_round_trip(tmp_path: Path) -> None:
    store = IncidentStore(tmp_path)
    assessment = InvestigationAssessment(
        incident_id="inc-orders-001",
        assessed_at=datetime(2026, 7, 17, 16, 0, tzinfo=UTC),
        assessed_by="operator",
        root_cause=RootCauseAssessment(
            operator_rationale="No root cause has been assessed.",
        ),
    )
    store.save_assessment(assessment)
    assert store.load_assessment(assessment.incident_id) == assessment
