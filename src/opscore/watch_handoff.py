from __future__ import annotations

from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field

from opscore.adapters.watch_run import WatchRun
from opscore.models import EvidenceItem

WATCH_HANDOFF_VERSION: Final = "watch.opscore/v1"


class WatchHandoff(BaseModel):
    """Versioned WATCH-to-OPSCORE evidence handoff envelope."""

    model_config = ConfigDict(extra="forbid")

    contract_version: Literal["watch.opscore/v1"] = WATCH_HANDOFF_VERSION
    target_reference: str = Field(min_length=1)
    source_location: str = Field(min_length=1)
    run: WatchRun


def evidence_from_handoff(handoff: WatchHandoff) -> list[EvidenceItem]:
    """Normalize one validated handoff into independently traceable evidence."""

    run = handoff.run
    raw_reference = f"WATCH:{run.run_id}@{handoff.source_location}"
    evidence: list[EvidenceItem] = []

    if run.observations.resolved_ips:
        evidence.append(
            EvidenceItem(
                evidence_id=f"ev-watch-{run.run_id}-dns",
                evidence_type="dns-resolution",
                source_system="WATCH handoff",
                collected_at=run.finished_at,
                target_reference=handoff.target_reference,
                normalized_data={
                    "resolved_ips": run.observations.resolved_ips,
                    "target_id": run.target_id,
                    "source_location": handoff.source_location,
                    "contract_version": handoff.contract_version,
                },
                raw_reference=raw_reference,
                limitations=["Evidence represents one bounded WATCH execution context."],
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
                source_system="WATCH handoff",
                collected_at=run.finished_at,
                target_reference=handoff.target_reference,
                normalized_data={
                    "status": run.observations.http_status,
                    "final_url": run.observations.final_url,
                    "redirect_count": run.observations.redirect_count,
                    "redirect_chain": run.observations.redirect_chain,
                    "response_ms": run.observations.response_ms,
                    "page_title": run.observations.page_title,
                    "error": "; ".join(run.observations.errors) or None,
                    "target_id": run.target_id,
                    "source_location": handoff.source_location,
                    "contract_version": handoff.contract_version,
                },
                raw_reference=raw_reference,
                collection_status="partial" if run.observations.errors else "completed",
                limitations=["WATCH evidence is an observation, not a root-cause conclusion."],
            )
        )

    if run.observations.tls_days_remaining is not None:
        evidence.append(
            EvidenceItem(
                evidence_id=f"ev-watch-{run.run_id}-tls",
                evidence_type="tls-certificate",
                source_system="WATCH handoff",
                collected_at=run.finished_at,
                target_reference=handoff.target_reference,
                normalized_data={
                    "days_remaining": run.observations.tls_days_remaining,
                    "target_id": run.target_id,
                    "source_location": handoff.source_location,
                    "contract_version": handoff.contract_version,
                },
                raw_reference=raw_reference,
                limitations=[
                    "Certificate evidence does not independently prove service impact."
                ],
            )
        )

    if not evidence:
        raise ValueError("WATCH handoff contains no supported observations")
    return evidence
