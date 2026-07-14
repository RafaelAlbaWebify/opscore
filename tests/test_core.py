import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from typer.testing import CliRunner

from opscore import __version__
from opscore.adapters.dns_audit import import_dns_audit_csv
from opscore.adapters.watch_run import import_watch_run
from opscore.analysis import analyze
from opscore.api import app as api_app
from opscore.cli import app as cli_app
from opscore.demo import load_bundle, run_demo
from opscore.imports import build_imported_bundle
from opscore.models import Incident, IncidentSeverity
from opscore.reports import render_json, render_markdown

SAMPLE = Path("samples/incidents/orders-service-unavailable.json")


def test_health_endpoint() -> None:
    response = TestClient(api_app).get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "opscore",
        "version": __version__,
    }


def test_demo_command(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        cli_app,
        ["demo", "--workspace", str(tmp_path), "--sample", str(SAMPLE)],
    )
    assert result.exit_code == 0
    assert "OPSCORE demo PASS" in result.stdout
    assert (tmp_path / "inc-orders-001.md").exists()


def test_correlate_command(tmp_path: Path) -> None:
    result = CliRunner().invoke(cli_app, ["correlate", "--workspace", str(tmp_path)])
    assert result.exit_code == 0
    assert "OPSCORE import correlation PASS" in result.stdout
    assert (tmp_path / "inc-orders-001-imported.md").exists()


def test_imported_bundle_produces_cross_source_findings() -> None:
    bundle = build_imported_bundle(
        SAMPLE,
        dns_csv_path=Path("samples/imports/dns-audit-sample.csv"),
        dns_collected_at=datetime(2026, 7, 14, 8, 8, tzinfo=UTC),
        watch_run_path=Path("samples/imports/watch-run-sample.json"),
        target_reference="orders-web",
    )
    analysis = analyze(bundle, generated_at=datetime(2026, 7, 14, 8, 9, tzinfo=UTC))
    codes = {finding.code for finding in analysis.findings}
    assert "DNS_OK_HTTP_UNAVAILABLE" in codes
    assert "DNS_FORWARD_REVERSE_REVIEW_REQUIRED" in codes
    assert "TLS_CERTIFICATE_EXPIRY_RISK" in codes
    assert all(item.raw_reference for item in analysis.evidence)


def test_incident_requires_timezone() -> None:
    with pytest.raises(ValidationError):
        Incident(
            incident_id="inc-test",
            title="Test",
            reported_symptom="Symptom",
            environment="sample",
            reported_at=datetime(2026, 1, 1),
            investigation_started_at=datetime(2026, 1, 1),
            affected_service_ids=["service-a"],
            severity=IncidentSeverity.HIGH,
        )


def test_reports_and_demo_are_valid_and_deterministic(tmp_path: Path) -> None:
    analysis = analyze(load_bundle(SAMPLE))
    report = render_markdown(analysis)
    assert "# OPSCORE Incident Evidence Report" in report
    assert "do not confirm root cause" in report
    payload = json.loads(render_json(analysis))
    assert payload["incident"]["incident_id"] == "inc-orders-001"
    first_md, first_json = run_demo(SAMPLE, tmp_path / "first")
    second_md, second_json = run_demo(SAMPLE, tmp_path / "second")
    assert first_md.read_text(encoding="utf-8") == second_md.read_text(encoding="utf-8")
    assert first_json.read_text(encoding="utf-8") == second_json.read_text(encoding="utf-8")


def test_dns_adapter_and_validation(tmp_path: Path) -> None:
    evidence = import_dns_audit_csv(
        Path("samples/imports/dns-audit-sample.csv"),
        collected_at=datetime(2026, 7, 14, 8, 8, tzinfo=UTC),
        target_reference="orders-web",
    )
    assert len(evidence) == 2
    assert evidence[0].raw_reference == "dns-audit-sample.csv:row-2"
    invalid = tmp_path / "invalid.csv"
    invalid.write_text("Finding,RecordName\nMissing PTR,orders\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing required columns"):
        import_dns_audit_csv(
            invalid,
            collected_at=datetime(2026, 7, 14, tzinfo=UTC),
            target_reference="orders-web",
        )


def test_watch_adapter_and_validation(tmp_path: Path) -> None:
    evidence = import_watch_run(
        Path("samples/imports/watch-run-sample.json"), target_reference="orders-web"
    )
    assert [item.evidence_type for item in evidence] == [
        "dns-resolution",
        "http-response",
        "tls-certificate",
    ]
    assert evidence[1].collection_status == "partial"
    payload = {
        "run_id": "run-empty",
        "target_id": "empty",
        "started_at": "2026-07-14T08:00:00Z",
        "finished_at": "2026-07-14T08:01:00Z",
        "status": "completed",
        "observations": {},
    }
    empty = tmp_path / "empty.json"
    empty.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="no supported observations"):
        import_watch_run(empty, target_reference="orders-web")