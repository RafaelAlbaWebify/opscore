import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from opscore.assessment import InvestigationAssessment, RootCauseAssessment
from opscore.history import IncidentHistoryStore, RevisionType
from opscore.storage import IncidentStore


def test_assessment_save_appends_immutable_revision(tmp_path: Path) -> None:
    store = IncidentStore(tmp_path)
    first = InvestigationAssessment(
        incident_id="inc-example",
        assessed_at=datetime(2026, 7, 17, 16, 0, tzinfo=UTC),
        assessed_by="operator",
        root_cause=RootCauseAssessment(operator_rationale="Not assessed."),
    )
    second = first.model_copy(
        update={
            "assessed_at": datetime(2026, 7, 17, 16, 5, tzinfo=UTC),
            "root_cause": RootCauseAssessment(
                statement="Candidate cause.",
                operator_rationale="New evidence changed the assessment.",
            ),
        }
    )
    store.save_assessment(first)
    store.save_assessment(second)

    revisions = store.list_revisions("inc-example")
    assert [item.revision_type for item in revisions] == [
        RevisionType.ASSESSMENT,
        RevisionType.ASSESSMENT,
    ]
    assert store.get_revision("inc-example", 1).payload == first.model_dump(mode="json")
    assert store.load_assessment("inc-example") == second


def test_m8_history_schema_migrates_without_data_loss(tmp_path: Path) -> None:
    database = tmp_path / "incident-history.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            CREATE TABLE incident_revisions (
                incident_id TEXT NOT NULL,
                revision_number INTEGER NOT NULL,
                revision_type TEXT NOT NULL CHECK (
                    revision_type IN ('bundle', 'analysis')
                ),
                created_at TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                PRIMARY KEY (incident_id, revision_number)
            )
            """
        )
        connection.execute(
            """
            INSERT INTO incident_revisions VALUES (?, ?, ?, ?, ?)
            """,
            (
                "inc-example",
                1,
                "bundle",
                "2026-07-17T16:00:00+00:00",
                '{"incident":{"incident_id":"inc-example"}}',
            ),
        )

    history = IncidentHistoryStore(tmp_path)
    assert history.get_revision("inc-example", 1) is not None
    metadata = history.append(
        "inc-example",
        RevisionType.ASSESSMENT,
        {"incident_id": "inc-example"},
    )
    assert metadata.revision_number == 2
