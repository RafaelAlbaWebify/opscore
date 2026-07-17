from pathlib import Path

from fastapi.testclient import TestClient

from opscore.api import create_app
from opscore.demo import load_bundle
from opscore.models import IncidentAnalysis, IncidentBundle

SAMPLE = Path("samples/incidents/orders-service-unavailable.json")


def test_incident_history_api_round_trip(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    bundle = load_bundle(SAMPLE)
    payload = bundle.model_dump(mode="json")

    assert client.post("/api/incidents", json=payload).status_code == 201
    analyzed = client.post("/api/incidents/inc-orders-001/analyze")
    assert analyzed.status_code == 200

    history = client.get("/api/incidents/inc-orders-001/history")
    assert history.status_code == 200
    assert [item["revision_number"] for item in history.json()] == [1, 2]
    assert [item["revision_type"] for item in history.json()] == [
        "bundle",
        "analysis",
    ]

    first = client.get("/api/incidents/inc-orders-001/history/1")
    second = client.get("/api/incidents/inc-orders-001/history/2")
    assert first.status_code == 200
    assert second.status_code == 200
    assert IncidentBundle.model_validate(first.json()["payload"]) == bundle
    assert IncidentAnalysis.model_validate(second.json()["payload"])


def test_incident_history_api_is_read_only(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    bundle = load_bundle(SAMPLE)
    assert client.post(
        "/api/incidents", json=bundle.model_dump(mode="json")
    ).status_code == 201
    database = tmp_path / "incident-history.sqlite3"
    before = database.read_bytes()

    assert client.get("/api/incidents/inc-orders-001/history").status_code == 200
    assert client.get("/api/incidents/inc-orders-001/history/1").status_code == 200

    assert database.read_bytes() == before


def test_incident_history_api_rejects_invalid_identifiers(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))

    assert client.get("/api/incidents/invalid/history").status_code == 422
    assert client.get("/api/incidents/inc-valid/history/0").status_code == 422
    assert client.get("/api/incidents/inc-valid/history/1").status_code == 404
