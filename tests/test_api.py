from pathlib import Path

from fastapi.testclient import TestClient

from opscore.api import create_app
from opscore.demo import load_bundle

SAMPLE = Path("samples/incidents/orders-service-unavailable.json")


def test_health_endpoint(tmp_path: Path) -> None:
    response = TestClient(create_app(tmp_path)).get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "opscore", "version": "0.2.0"}


def test_incident_api_lifecycle(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    bundle = load_bundle(SAMPLE)
    payload = bundle.model_dump(mode="json")

    assert client.post("/api/incidents", json=payload).status_code == 201
    assert client.post("/api/incidents", json=payload).status_code == 409
    assert client.get("/api/incidents").json()[0]["incident_id"] == "inc-orders-001"
    assert client.get("/api/incidents/inc-orders-001").json() == payload

    evidence = {
        "evidence_id": "ev-operator-note-001",
        "evidence_type": "operator-observation",
        "source_system": "operator",
        "collected_at": "2026-01-15T10:04:00Z",
        "target_reference": "orders-web",
        "normalized_data": {"note": "Service owner contacted."},
        "raw_reference": None,
        "collection_status": "completed",
        "limitations": ["Operator statement not independently verified."],
    }
    added = client.post("/api/incidents/inc-orders-001/evidence", json=evidence)
    assert added.status_code == 201
    assert added.json()["evidence"][-1]["evidence_id"] == "ev-operator-note-001"
    assert client.post("/api/incidents/inc-orders-001/evidence", json=evidence).status_code == 409

    analyzed = client.post("/api/incidents/inc-orders-001/analyze")
    assert analyzed.status_code == 200
    assert analyzed.json()["incident"]["root_cause_status"] == "unassessed"
    assert client.get("/api/incidents/inc-orders-001/analysis").json() == analyzed.json()

    report = client.get("/api/incidents/inc-orders-001/report.md")
    assert report.status_code == 200
    assert report.headers["content-type"].startswith("text/markdown")
    assert "OPSCORE Incident Evidence Report" in report.text


def test_incident_api_not_found(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    assert client.get("/api/incidents/inc-missing").status_code == 404
    assert client.post("/api/incidents/inc-missing/analyze").status_code == 404
    assert client.get("/api/incidents/inc-missing/analysis").status_code == 404
    assert client.get("/api/incidents/inc-missing/report.md").status_code == 404
