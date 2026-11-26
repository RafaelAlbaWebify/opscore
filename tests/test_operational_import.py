import json
from pathlib import Path

from fastapi.testclient import TestClient

from opscore.api import create_app
from opscore.demo import load_bundle
from opscore.operational_import import OperationalImport, normalize_import

SAMPLE = Path("samples/incidents/orders-service-unavailable.json")


def test_operational_import_lifecycle(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    bundle = load_bundle(SAMPLE)
    assert client.post("/api/incidents", json=bundle.model_dump(mode="json")).status_code == 201
    endpoint = "/api/incidents/inc-orders-001/operational-import"
    secret = "FAKE_SECRET_DO_NOT_STORE"
    cases = [
        ("application-log", [{"status_code": 503, "message": "timeout " + secret}]),
        ("windows-event", [
            {"event_id": 7000, "provider": "Winlogon", "message": secret},
            {"event_id": 7031, "provider": "Service Control Manager"},
        ]),
        ("iis", {"services": [{"name": "W3SVC", "status": "Stopped"}],
                 "sites": [{"name": secret, "state": "Stopped"}]}),
    ]
    for kind, payload in cases:
        request = {
            "kind": kind, "target_reference": "orders-web",
            "collected_at": "2026-07-14T08:10:00Z", "content": json.dumps(payload),
        }
        response = client.post(endpoint, json=request)
        assert response.status_code == 201
        assert secret not in response.text
        assert client.post(endpoint, json=request).status_code == 409
    analysis = client.post("/api/incidents/inc-orders-001/analyze")
    assert analysis.status_code == 200
    findings = analysis.json()["findings"]
    codes = {finding["code"] for finding in findings}
    assert codes >= {"APP_HTTP_5XX", "APP_TIMEOUT", "WIN_SERVICE_FAILURE",
                     "IIS_SERVICE_STOPPED", "IIS_SITE_STOPPED"}
    service = next(f for f in findings if f["code"] == "WIN_SERVICE_FAILURE")
    assert service["statement"].endswith(": 1.")
    report = client.get("/api/incidents/inc-orders-001/report.md")
    assert "APP_HTTP_5XX" in report.text
    assert secret not in report.text
    for path in tmp_path.rglob("*"):
        if path.is_file():
            assert secret.encode() not in path.read_bytes()


def test_invalid_operational_import_does_not_echo_content(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    bundle = load_bundle(SAMPLE)
    assert client.post("/api/incidents", json=bundle.model_dump(mode="json")).status_code == 201
    response = client.post("/api/incidents/inc-orders-001/operational-import", json={
        "kind": "application-log", "target_reference": "orders-web",
        "collected_at": "2026-07-14T08:10:00Z", "content": "FAKE_SECRET_INVALID_JSON",
    })
    assert response.status_code == 422
    assert "FAKE_SECRET_INVALID_JSON" not in response.text


def test_validation_error_does_not_echo_invalid_body(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    response = client.post("/api/incidents/inc-orders-001/operational-import", json={
        "kind": "FAKE_SECRET_INVALID_KIND",
        "content": "FAKE_SECRET_INVALID_BODY",
    })
    assert response.status_code == 422
    assert "FAKE_SECRET" not in response.text


def test_operator_import_controls_present(tmp_path: Path) -> None:
    response = TestClient(create_app(tmp_path)).get("/")
    assert response.status_code == 200
    assert "operational-import-form" in response.text
    assert "operational-file" in response.text


def test_original_custosops_samples() -> None:
    for kind, filename, expected in [
        ("application-log", "fastapi-api-errors.log", {
            "APP_HTTP_5XX": 1, "APP_AUTH_FAILURE": 2, "APP_DNS": 1,
            "APP_TLS": 1, "APP_DATABASE": 1, "APP_NOT_FOUND": 2,
            "APP_SLOW_REQUEST": 1, "APP_SENSITIVE_INDICATOR": 2,
        }),
        ("windows-event", "sample-windows-events.json", {
            "WIN_SERVICE_FAILURE": 1, "WIN_FAILED_LOGON": 1,
            "WIN_APPLICATION_ERROR": 1, "WIN_DNS_ERROR": 1,
            "WIN_REBOOT": 1, "WIN_UPDATE": 1,
        }),
    ]:
        content = (Path("samples/imports/custosops") / filename).read_text(encoding="utf-8")
        evidence = normalize_import(OperationalImport.model_validate({
            "kind": kind, "target_reference": "orders-web",
            "collected_at": "2026-07-14T08:10:00Z", "content": content,
            "input_format": "text" if filename.endswith(".log") else "json",
        }))
        counts = evidence.normalized_data["signal_counts"]
        assert all(counts.get(code) == count for code, count in expected.items())
        assert "SYNTHETIC_REDACTED_VALUE" not in evidence.model_dump_json()
        assert "LAB-WIN11-01" not in evidence.model_dump_json()


def test_iis_evidence_envelope() -> None:
    evidence = normalize_import(OperationalImport.model_validate({
        "kind": "iis", "target_reference": "orders-web",
        "collected_at": "2026-07-14T08:10:00Z",
        "content": json.dumps({"evidence": {
            "services": [{"name": "W3SVC", "status": "Stopped"}],
            "sites": [{"state": "Stopped"}],
            "application_pools": [{"state": "Stopped"}],
        }}),
    }))
    assert evidence.normalized_data["signal_counts"] == {
        "IIS_SERVICE_STOPPED": 1, "IIS_SITE_STOPPED": 1, "IIS_POOL_STOPPED": 1,
    }
