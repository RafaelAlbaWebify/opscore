from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from opscore.models import EvidenceItem


class BackupAwarenessRecord(BaseModel):
    """Operator-supplied backup context for one incident service."""

    model_config = ConfigDict(extra="forbid")

    target_reference: str = Field(min_length=1)
    source_system: str = Field(min_length=1)
    source_location: str = Field(min_length=1)
    protection_status: Literal["protected", "degraded", "unprotected", "unknown"]
    last_successful_backup_at: datetime | None = None
    last_restore_test_at: datetime | None = None
    recovery_point_objective_minutes: int | None = Field(default=None, ge=0)
    recovery_time_objective_minutes: int | None = Field(default=None, ge=0)
    retention_summary: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("last_successful_backup_at", "last_restore_test_at")
    @classmethod
    def normalize_timestamp(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("backup-awareness timestamps must include a timezone")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_status_context(self) -> BackupAwarenessRecord:
        if self.protection_status == "protected" and self.last_successful_backup_at is None:
            raise ValueError(
                "protected status requires last_successful_backup_at evidence"
            )
        return self


def evidence_from_backup_record(record: BackupAwarenessRecord) -> EvidenceItem:
    """Normalize one operator-supplied backup record into traceable evidence."""

    collected_at = datetime.now(UTC)
    limitations = [
        "Backup-awareness evidence does not execute or verify a backup or restore operation.",
        "Protection status is limited to the supplied source record and collection time.",
    ]
    if record.last_restore_test_at is None:
        limitations.append("No restore-test timestamp was supplied.")

    return EvidenceItem(
        evidence_id=f"ev-backup-{uuid4().hex[:12]}",
        evidence_type="backup-awareness",
        source_system=record.source_system,
        collected_at=collected_at,
        target_reference=record.target_reference,
        normalized_data={
            "source_location": record.source_location,
            "protection_status": record.protection_status,
            "last_successful_backup_at": (
                record.last_successful_backup_at.isoformat()
                if record.last_successful_backup_at
                else None
            ),
            "last_restore_test_at": (
                record.last_restore_test_at.isoformat()
                if record.last_restore_test_at
                else None
            ),
            "recovery_point_objective_minutes": (
                record.recovery_point_objective_minutes
            ),
            "recovery_time_objective_minutes": (
                record.recovery_time_objective_minutes
            ),
            "retention_summary": record.retention_summary,
            "notes": record.notes,
        },
        collection_status=(
            "completed" if record.protection_status != "unknown" else "partial"
        ),
        limitations=limitations,
    )
