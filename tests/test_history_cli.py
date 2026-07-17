import json
from pathlib import Path

from typer.testing import CliRunner

from opscore.cli import app
from opscore.demo import load_bundle
from opscore.storage import IncidentStore

SAMPLE = Path("samples/incidents/orders-service-unavailable.json")


def test_history_cli_lists_and_retrieves_revisions(tmp_path: Path) -> None:
    store = IncidentStore(tmp_path)
    bundle = load_bundle(SAMPLE)
    store.save_bundle(bundle)

    runner = CliRunner()
    listed = runner.invoke(
        app,
        ["history", bundle.incident.incident_id, "--workspace", str(tmp_path)],
    )
    assert listed.exit_code == 0
    metadata = json.loads(listed.stdout)
    assert metadata[0]["revision_number"] == 1
    assert metadata[0]["revision_type"] == "bundle"

    retrieved = runner.invoke(
        app,
        [
            "history",
            bundle.incident.incident_id,
            "--workspace",
            str(tmp_path),
            "--revision",
            "1",
        ],
    )
    assert retrieved.exit_code == 0
    revision = json.loads(retrieved.stdout)
    assert (
        revision["payload"]["incident"]["incident_id"]
        == bundle.incident.incident_id
    )


def test_history_cli_rejects_invalid_incident_id(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        app,
        ["history", "invalid", "--workspace", str(tmp_path)],
    )
    assert result.exit_code != 0
    assert "invalid incident identifier" in result.output
