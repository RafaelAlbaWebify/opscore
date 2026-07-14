from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from opscore.models import EvidenceItem


class WatchObservations(BaseModel):
    model_config = ConfigDict(extra="allow")
    http_status: int | None = Field(default=None, ge=100, le=599)
    final_url: str | None = None
    redirect_count: int | None = Field(default=None, ge=0)
    redirect_chain: list[str] = Field(default_factory=list)
    response_ms: int | None = Field(default=None, ge=0)
    tls_days_remaining: int | None = None
    page_title: str | None = None
    resolved_ips: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class WatchRun(BaseModel):
    model_config = ConfigDict(extra="allow")
    run_id: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    started_at: datetime
    finished_at: datetime
    status: str
    observations: WatchObservations

    @field_validator("started_at", "finished_at")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("WATCH timestamps must include a timezone")
        return value.astimezone(UTC)


def import_watch_run(path: Path, *, target_reference: str) -> list[EvidenceItem]:
    """Normalize one WATCH JSON run into independently traceable evidence items."""
    payload: Any = json.loads(path.read_text(encoding="utf-8"))
    run = WatchRun.model_validate(payload)
    raw_reference = f"{path.name}:{run.run_id}"
    evidence: list[EvidenceItem] = []

    if run.observations.resolved_ips:
        evidence.append(
            EvidenceItem(
                evidence_id=f"ev-watch-{run.run_id}-dns",
                evidence_type="dns-resolution",
                source_system="WATCH JSON run",
                collected_at=run.finished_at,
                target_reference=target_reference,
                normalized_data={
                    "resolved_ips": run.observations.resolved_ips,
                    "target_id": run.target_id,
                },
                raw_reference=raw_reference,
                limitations=[],
            )
        )

    http_present = (
        run.observations.http_status is not None
        or run.observations.final_url is not None
        or bool(run.observations.errors)
    )
    if http_present:
        evidence.append(
            EvidenceItem(
                evidence_id=f"ev-watch-{run.run_id}-http",
                evidence_type="http-response",
                source_system="WATCH JSON run",
                collected_at=run.finished_at,
                target_reference=target_reference,
                normalized_data={
                    "status": run.observations.http_status,
                    "final_url": run.observations.final_url,
                    "redirect_count": run.observations.redirect_count,
                    "redirect_chain": run.observations.redirect_chain,
                    "response_ms": run.observations.response_ms,
                    "page_title": run.observations.page_title,
                    "error": "; ".join(run.observations.errors) or None,
                },
                raw_reference=raw_reference,
                collection_status=("partial" if run.observations.errors else "completed"),
                limitations=[
                    "WATCH evidence describes one bounded collection run and source path."
                ],
            )
        )

    if run.observations.tls_days_remaining is not None:
        evidence.append(
            EvidenceItem(
                evidence_id=f"ev-watch-{run.run_id}-tls",
                evidence_type="tls-certificate",
                source_system="WATCH JSON run",
                collected_at=run.finished_at,
                target_reference=target_reference,
                normalized_data={
                    "days_remaining": run.observations.tls_days_remaining,
                    "target_id": run.target_id,
                },
                raw_reference=raw_reference,
                limitations=[
                    "Certificate evidence does not by itself prove current service impact."
                ],
            )
        )

    if not evidence:
        raise ValueError("WATCH run contains no supported observations")
    return evidence
