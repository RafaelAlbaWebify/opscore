from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from opscore.api import create_app
from opscore.backup_awareness import BackupAwarenessRecord, evidence_from_backup_record
from opscore.demo import load_bundle

SAMPLE = Path("samples/incidents/orders-service-unavailable.json")


def backup_payload() -> dict[str, object]:
    return {
        "target_reference": "orders-web",
        "source_system": "synthetic-backup-console",
        "source_location": "pytest",
        "protection_status": "protected",
        "last_successful_backup_at": "2026-07-14T08:00:00Z",
        "last_restore_test_at": "2026-06-30T09:00:00Z",
        "recovery_point_objective_minutes": 60,
        "recovery_time_objective_minutes": 240,
        "retention_summary": "Synthetic daily retention summary.",
        "notes": "Public-safe sample only.",
    }


def test_protected_status_requires_success_timestamp() -> None:
    payload = backup_payload()
    payload["last_successful_backup_at"] = None
    with pytest.raises(ValidationError):
        BackupAwarenessRecord.model_validate(payload)


def test_backup_record_normalizes_traceable_evidence() -> None:
    record = BackupAwarenessRecord.model_validate(backup_payload())
    evidence = evidence_from_backup_record(record)
    assert evidence.evidence_type == "backup-awareness"
    assert evidence.target_reference == "orders-web"
    assert evidence.normalized_data["protection_status"] == "protected"
    assert evidence.normalized_data["recovery_point_objective_minutes"] == 60
    assert evidence.collection_status == "completed"


def test_unknown_status_is_partial_and_restore_gap_is_explicit() -> None:
    payload = backup_payload()
    payload["protection_status"] = "unknown"
    payload["last_successful_backup_at"] = None
    payload["last_restore_test_at"] = None
    evidence = evidence_from_backup_record(BackupAwarenessRecord.model_validate(payload))
    assert evidence.collection_status == "partial"
    assert "No restore-test timestamp was supplied." in evidence.limitations


def test_backup_awareness_incident_endpoint(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    bundle = load_bundle(SAMPLE).model_dump(mode="json")
    assert client.post("/api/incidents", json=bundle).status_code == 201

    endpoint = "/api/incidents/inc-orders-001/backup-awareness"
    response = client.post(endpoint, json=backup_payload())
    assert response.status_code == 201
    assert response.json()["evidence"][-1]["evidence_type"] == "backup-awareness"

    payload = backup_payload()
    payload["target_reference"] = "unknown-service"
    assert client.post(endpoint, json=payload).status_code == 422
