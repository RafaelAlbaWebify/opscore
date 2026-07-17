from pathlib import Path

import pytest

from opscore.analysis import analyze
from opscore.demo import load_bundle
from opscore.history import RevisionType
from opscore.models import IncidentBundle
from opscore.storage import IncidentStore

SAMPLE = Path("samples/incidents/orders-service-unavailable.json")


def test_bundle_and_analysis_revisions_are_ordered_and_immutable(
    tmp_path: Path,
) -> None:
    store = IncidentStore(tmp_path)
    original = load_bundle(SAMPLE)

    store.save_bundle(original)
    updated = original.model_copy(
        update={
            "incident": original.incident.model_copy(
                update={"title": "Updated incident title"}
            )
        }
    )
    store.save_bundle(updated)
    analysis = analyze(updated)
    store.save_analysis(analysis)

    revisions = store.list_revisions(original.incident.incident_id)
    assert [revision.revision_number for revision in revisions] == [1, 2, 3]
    assert [revision.revision_type for revision in revisions] == [
        RevisionType.BUNDLE,
        RevisionType.BUNDLE,
        RevisionType.ANALYSIS,
    ]

    first = store.get_revision(original.incident.incident_id, 1)
    second = store.get_revision(original.incident.incident_id, 2)
    third = store.get_revision(original.incident.incident_id, 3)

    assert first is not None
    assert second is not None
    assert third is not None
    assert IncidentBundle.model_validate(first.payload) == original
    assert IncidentBundle.model_validate(second.payload) == updated
    assert first.payload["incident"]["title"] != second.payload["incident"]["title"]
    assert third.revision_type is RevisionType.ANALYSIS


def test_history_bootstrap_does_not_modify_existing_json(tmp_path: Path) -> None:
    incidents = tmp_path / "incidents"
    incidents.mkdir(parents=True)
    existing = incidents / "inc-existing.json"
    existing.write_text('{"unchanged": true}', encoding="utf-8")
    before = existing.read_bytes()

    IncidentStore(tmp_path)

    assert existing.read_bytes() == before
    assert (tmp_path / "incident-history.sqlite3").exists()


def test_history_reads_do_not_change_database(tmp_path: Path) -> None:
    store = IncidentStore(tmp_path)
    bundle = load_bundle(SAMPLE)
    store.save_bundle(bundle)
    database = tmp_path / "incident-history.sqlite3"
    before = database.read_bytes()

    assert store.list_revisions(bundle.incident.incident_id)
    assert store.get_revision(bundle.incident.incident_id, 1) is not None

    assert database.read_bytes() == before


@pytest.mark.parametrize("incident_id", ["../escape", "invalid", "inc-UPPER"])
def test_history_rejects_invalid_incident_identifiers(
    tmp_path: Path, incident_id: str
) -> None:
    store = IncidentStore(tmp_path)

    with pytest.raises(ValueError, match="invalid incident identifier"):
        store.list_revisions(incident_id)


def test_history_rejects_non_positive_revision_number(tmp_path: Path) -> None:
    store = IncidentStore(tmp_path)

    with pytest.raises(ValueError, match="revision number must be positive"):
        store.get_revision("inc-valid", 0)
