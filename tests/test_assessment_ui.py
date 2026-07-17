from pathlib import Path

from fastapi.testclient import TestClient

from opscore.api import create_app


def test_operator_interface_exposes_assessment_panel(tmp_path: Path) -> None:
    response = TestClient(create_app(tmp_path)).get("/")
    assert response.status_code == 200
    assert "Operator assessment" in response.text
    assert "load-assessment" in response.text
