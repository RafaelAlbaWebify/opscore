from __future__ import annotations

import json
import re
import sqlite3
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

_INCIDENT_ID = re.compile(r"^inc-[a-z0-9-]+$")


class RevisionType(StrEnum):
    BUNDLE = "bundle"
    ANALYSIS = "analysis"
    ASSESSMENT = "assessment"


class IncidentRevisionMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    incident_id: str
    revision_number: int = Field(ge=1)
    revision_type: RevisionType
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("revision timestamps must include a timezone")
        return value.astimezone(UTC)


class IncidentRevision(IncidentRevisionMetadata):
    payload: dict[str, Any]


class IncidentHistoryStore:
    """Append-only SQLite history for validated incident payloads."""

    def __init__(self, workspace: Path) -> None:
        workspace.mkdir(parents=True, exist_ok=True)
        self.database_path = workspace / "incident-history.sqlite3"
        self._bootstrap()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _create_schema(connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE incident_revisions (
                incident_id TEXT NOT NULL,
                revision_number INTEGER NOT NULL,
                revision_type TEXT NOT NULL CHECK (
                    revision_type IN ('bundle', 'analysis', 'assessment')
                ),
                created_at TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                PRIMARY KEY (incident_id, revision_number)
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX idx_incident_revisions_type
            ON incident_revisions (incident_id, revision_type, revision_number)
            """
        )

    def _bootstrap(self) -> None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT sql FROM sqlite_master
                WHERE type = 'table' AND name = 'incident_revisions'
                """
            ).fetchone()
            if row is None:
                self._create_schema(connection)
                return
            schema_sql = str(row["sql"] or "")
            if "'assessment'" in schema_sql:
                connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_incident_revisions_type
                    ON incident_revisions (incident_id, revision_type, revision_number)
                    """
                )
                return
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    "ALTER TABLE incident_revisions RENAME TO incident_revisions_m8"
                )
                connection.execute("DROP INDEX IF EXISTS idx_incident_revisions_type")
                self._create_schema(connection)
                connection.execute(
                    """
                    INSERT INTO incident_revisions (
                        incident_id, revision_number, revision_type,
                        created_at, payload_json
                    )
                    SELECT incident_id, revision_number, revision_type,
                           created_at, payload_json
                    FROM incident_revisions_m8
                    """
                )
                connection.execute("DROP TABLE incident_revisions_m8")
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def validate_incident_id(incident_id: str) -> None:
        if _INCIDENT_ID.fullmatch(incident_id) is None:
            raise ValueError("invalid incident identifier")

    def append(
        self,
        incident_id: str,
        revision_type: RevisionType,
        payload: dict[str, Any],
        *,
        created_at: datetime | None = None,
        connection: sqlite3.Connection | None = None,
    ) -> IncidentRevisionMetadata:
        self.validate_incident_id(incident_id)
        timestamp = (created_at or datetime.now(UTC)).astimezone(UTC)
        owns_connection = connection is None
        active = connection or self._connect()
        try:
            if owns_connection:
                active.execute("BEGIN IMMEDIATE")
            row = active.execute(
                """
                SELECT COALESCE(MAX(revision_number), 0) + 1 AS next_revision
                FROM incident_revisions
                WHERE incident_id = ?
                """,
                (incident_id,),
            ).fetchone()
            revision_number = int(row["next_revision"])
            active.execute(
                """
                INSERT INTO incident_revisions (
                    incident_id,
                    revision_number,
                    revision_type,
                    created_at,
                    payload_json
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    incident_id,
                    revision_number,
                    revision_type.value,
                    timestamp.isoformat(),
                    json.dumps(payload, sort_keys=True, separators=(",", ":")),
                ),
            )
            if owns_connection:
                active.commit()
        except Exception:
            if owns_connection:
                active.rollback()
            raise
        finally:
            if owns_connection:
                active.close()
        return IncidentRevisionMetadata(
            incident_id=incident_id,
            revision_number=revision_number,
            revision_type=revision_type,
            created_at=timestamp,
        )

    def list_revisions(self, incident_id: str) -> list[IncidentRevisionMetadata]:
        self.validate_incident_id(incident_id)
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT incident_id, revision_number, revision_type, created_at
                FROM incident_revisions
                WHERE incident_id = ?
                ORDER BY revision_number
                """,
                (incident_id,),
            ).fetchall()
        return [
            IncidentRevisionMetadata(
                incident_id=row["incident_id"],
                revision_number=row["revision_number"],
                revision_type=RevisionType(row["revision_type"]),
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    def get_revision(
        self, incident_id: str, revision_number: int
    ) -> IncidentRevision | None:
        self.validate_incident_id(incident_id)
        if revision_number < 1:
            raise ValueError("revision number must be positive")
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT incident_id, revision_number, revision_type, created_at,
                       payload_json
                FROM incident_revisions
                WHERE incident_id = ? AND revision_number = ?
                """,
                (incident_id, revision_number),
            ).fetchone()
        if row is None:
            return None
        return IncidentRevision(
            incident_id=row["incident_id"],
            revision_number=row["revision_number"],
            revision_type=RevisionType(row["revision_type"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            payload=json.loads(row["payload_json"]),
        )
