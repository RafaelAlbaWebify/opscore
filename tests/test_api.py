from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from opscore import __version__
from opscore.api import create_app
from opscore.demo import load_bundle
from opscore.models import EvidenceItem

SAMPLE = Path("samples/incidents/orders-service-unavailable.json")


def test_operator_interface(tmp_path: Path) -> None:
    response = TestClient(create_app(tmp_path)).get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "OPSCORE Operator Workbench" in response.text
    assert "New incident" in response.text
    assert "Evidence inventory" in response.text
    assert "Run deterministic analysis" in response.text
    assert 'request("/api/incidents")' in response.text


def test_health_endpoint(tmp_path: Path) -> None:
    response = TestClient(create_app(tmp_path)).get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "opscore", "version": __version__}


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


def test_bounded_collection_endpoint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def synthetic_collection(request: object) -> list[EvidenceItem]:
        return [
            EvidenceItem(
                evidence_id="ev-live-dns-test",
                evidence_type="dns-resolution",
                source_system="opscore-bounded-collector",
                collected_at=datetime(2026, 7, 14, 10, 0, tzinfo=UTC),
                target_reference="orders-web",
                normalized_data={"resolved_ips": ["192.0.2.10"]},
            )
        ]

    monkeypatch.setattr("opscore.api.collect_target", synthetic_collection)
    client = TestClient(create_app(tmp_path))
    payload = load_bundle(SAMPLE).model_dump(mode="json")
    assert client.post("/api/incidents", json=payload).status_code == 201

    request = {
        "url": "https://orders.example.test/health",
        "target_reference": "orders-web",
        "source_location": "pytest",
        "timeout_seconds": 2,
    }
    collected = client.post("/api/incidents/inc-orders-001/collect", json=request)
    assert collected.status_code == 201
    assert collected.json()["evidence"][-1]["evidence_id"] == "ev-live-dns-test"

    request["target_reference"] = "unknown-service"
    assert client.post("/api/incidents/inc-orders-001/collect", json=request).status_code == 422


def test_incident_api_not_found(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    assert client.get("/api/incidents/inc-missing").status_code == 404
    assert client.post("/api/incidents/inc-missing/analyze").status_code == 404
    assert client.post(
        "/api/incidents/inc-missing/collect",
        json={
            "url": "https://example.test",
            "target_reference": "service-web",
            "source_location": "pytest",
        },
    ).status_code == 404
    assert client.post(
        "/api/incidents/inc-missing/connectivity",
        json={
            "host": "example.test",
            "port": 443,
            "target_reference": "service-web",
            "source_location": "pytest",
        },
    ).status_code == 404
    assert client.post(
        "/api/incidents/inc-missing/watch-handoff",
        json={
            "contract_version": "watch.opscore/v1",
            "target_reference": "service-web",
            "source_location": "pytest",
            "run": {
                "run_id": "missing-001",
                "target_id": "service-web",
                "started_at": "2026-07-14T10:00:00Z",
                "finished_at": "2026-07-14T10:00:01Z",
                "status": "completed",
                "observations": {"http_status": 200},
            },
        },
    ).status_code == 404
    assert client.get("/api/incidents/inc-missing/analysis").status_code == 404
    assert client.get("/api/incidents/inc-missing/report.md").status_code == 404


def test_openapi_incident_contract(tmp_path: Path) -> None:
    paths = create_app(tmp_path).openapi()["paths"]
    expected_methods = {
        "/api/health": {"get"},
        "/api/incidents": {"get", "post"},
        "/api/incidents/{incident_id}": {"get"},
        "/api/incidents/{incident_id}/evidence": {"post"},
        "/api/incidents/{incident_id}/collect": {"post"},
        "/api/incidents/{incident_id}/connectivity": {"post"},
        "/api/incidents/{incident_id}/watch-handoff": {"post"},
        "/api/incidents/{incident_id}/analyze": {"post"},
        "/api/incidents/{incident_id}/analysis": {"get"},
        "/api/incidents/{incident_id}/report.md": {"get"},
    }
    assert set(paths) == set(expected_methods)
    for path, methods in expected_methods.items():
        assert set(paths[path]) == methods
