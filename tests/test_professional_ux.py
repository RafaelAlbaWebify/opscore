from pathlib import Path

from fastapi.testclient import TestClient

from opscore.api import create_app


def test_operator_interface_exposes_progressive_professional_workflow(tmp_path: Path) -> None:
    response = TestClient(create_app(tmp_path)).get("/")

    assert response.status_code == 200
    assert 'id="opscore-ux-polish"' in response.text
    assert 'aria-label="Active incident workflow"' in response.text
    assert 'toggle.id = "toggle-intake"' in response.text
    assert 'role="status" aria-live="polite"' in response.text
    assert 'class="skip-link"' in response.text
    assert "No operator assessment has been recorded" in response.text


def test_operator_interface_keeps_safe_report_rendering_and_api_contracts(tmp_path: Path) -> None:
    response = TestClient(create_app(tmp_path)).get("/")

    assert response.status_code == 200
    assert 'reportRendered.className = "report-rendered"' in response.text
    assert "escapeText(line" in response.text
    assert 'request("/api/incidents")' in response.text
    assert "/assessment`" in response.text
    assert "Run deterministic analysis" in response.text
