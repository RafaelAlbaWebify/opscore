from pathlib import Path

from opscore.analysis import analyze
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
