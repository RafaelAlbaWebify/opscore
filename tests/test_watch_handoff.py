from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from typer.testing import CliRunner

from opscore.api import create_app
from opscore.cli import app
from opscore.demo import load_bundle
from opscore.watch_handoff import WatchHandoff, evidence_from_handoff

SAMPLE = Path("samples/incidents/orders-service-unavailable.json")
HANDOFF_SAMPLE = Path("samples/imports/watch-handoff-v1.json")


def handoff_payload() -> dict[str, object]:
    return {
        "contract_version": "watch.opscore/v1",
        "target_reference": "orders-web",
        "source_location": "watch-local-runner",
        "run": {
            "run_id": "run-001",
            "target_id": "orders-public",
            "started_at": "2026-07-14T10:00:00Z",
            "finished_at": "2026-07-14T10:00:02Z",
            "status": "completed",
            "observations": {
                "http_status": 503,
                "final_url": "https://orders.example.test/health",
                "redirect_count": 0,
                "redirect_chain": [],
                "response_ms": 231,
                "tls_days_remaining": 18,
                "page_title": None,
                "resolved_ips": ["192.0.2.10"],
                "errors": [],
            },
        },
    }


def test_handoff_rejects_unknown_contract_version() -> None:
    payload = handoff_payload()
    payload["contract_version"] = "watch.opscore/v2"
    with pytest.raises(ValidationError):
        WatchHandoff.model_validate(payload)


def test_handoff_normalizes_traceable_evidence() -> None:
    evidence = evidence_from_handoff(WatchHandoff.model_validate(handoff_payload()))
    assert [item.evidence_type for item in evidence] == [
        "dns-resolution",
        "http-response",
        "tls-certificate",
    ]
    assert all(item.source_system == "WATCH handoff" for item in evidence)
    assert all(
        item.raw_reference == "WATCH:run-001@watch-local-runner"
        for item in evidence
    )
    assert all(
        item.normalized_data["contract_version"] == "watch.opscore/v1"
        for item in evidence
    )


def test_incident_watch_handoff_lifecycle(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    bundle = load_bundle(SAMPLE).model_dump(mode="json")
    assert client.post("/api/incidents", json=bundle).status_code == 201

    endpoint = "/api/incidents/inc-orders-001/watch-handoff"
    imported = client.post(endpoint, json=handoff_payload())
    assert imported.status_code == 201
    assert len(imported.json()["evidence"]) == len(bundle["evidence"]) + 3

    duplicate = client.post(endpoint, json=handoff_payload())
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "WATCH run already imported"

    unknown_service = handoff_payload()
    unknown_service["target_reference"] = "unknown-service"
    assert client.post(endpoint, json=unknown_service).status_code == 422


def test_handoff_requires_supported_observations(tmp_path: Path) -> None:
    payload = handoff_payload()
    run = payload["run"]
    assert isinstance(run, dict)
    run["observations"] = {
        "http_status": None,
        "final_url": None,
        "resolved_ips": [],
        "errors": [],
        "tls_days_remaining": None,
    }

    client = TestClient(create_app(tmp_path))
    bundle = load_bundle(SAMPLE).model_dump(mode="json")
    assert client.post("/api/incidents", json=bundle).status_code == 201
    response = client.post(
        "/api/incidents/inc-orders-001/watch-handoff",
        json=payload,
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "WATCH handoff contains no supported observations"


def test_watch_handoff_cli_exports_normalized_evidence(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        app,
        [
            "watch-handoff",
            "--handoff-file",
            str(HANDOFF_SAMPLE),
            "--workspace",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0
    assert "OPSCORE WATCH handoff PASS" in result.stdout
    assert "watch.opscore/v1" in result.stdout
    assert (tmp_path / "watch-run-001-evidence.json").exists()
