from pathlib import Path

from fastapi.testclient import TestClient

from opscore.api import create_app


def test_operator_interface_uses_trace_aligned_shell(tmp_path: Path) -> None:
    response = TestClient(create_app(tmp_path)).get("/")

    assert response.status_code == 200
    assert 'id="opscore-visual-refresh"' in response.text
    assert "OPSCORE\\A INCIDENT EVIDENCE" in response.text
    assert 'class="ops-nav"' in response.text
    assert "Read-only investigation boundary" in response.text
    assert "color-scheme: light" in response.text


def test_operator_interface_exposes_data_backed_overview(tmp_path: Path) -> None:
    response = TestClient(create_app(tmp_path)).get("/")

    assert response.status_code == 200
    assert 'id="operations-overview"' in response.text
    assert 'id="metric-total"' in response.text
    assert 'id="incident-search"' in response.text
    assert 'id="incident-register-body"' in response.text
    assert 'request("/api/incidents")' in response.text
