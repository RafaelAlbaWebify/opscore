from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from opscore.models import EvidenceItem

_REQUIRED_COLUMNS = {
    "Zone",
    "RecordName",
    "RecordType",
    "IPAddress",
    "Finding",
    "Severity",
    "RecommendedAction",
}


def import_dns_audit_csv(
    path: Path,
    *,
    collected_at: datetime,
    target_reference: str,
) -> list[EvidenceItem]:
    """Normalize DNS Audit Tool rows into evidence items."""
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = sorted(_REQUIRED_COLUMNS - columns)
        if missing:
            raise ValueError(f"DNS audit CSV missing required columns: {missing}")

        evidence: list[EvidenceItem] = []
        for row_number, row in enumerate(reader, start=2):
            finding = (row.get("Finding") or "").strip()
            record_name = (row.get("RecordName") or "").strip()
            if not finding or not record_name:
                raise ValueError(
                    f"DNS audit CSV row {row_number} requires Finding and RecordName"
                )
            evidence.append(
                EvidenceItem(
                    evidence_id=f"ev-dns-audit-{row_number - 1}",
                    evidence_type="dns-audit-finding",
                    source_system="DNS Audit Tool CSV",
                    collected_at=collected_at,
                    target_reference=target_reference,
                    normalized_data={
                        "zone": (row.get("Zone") or "").strip(),
                        "record_name": record_name,
                        "record_type": (row.get("RecordType") or "").strip(),
                        "ip_address": (row.get("IPAddress") or "").strip(),
                        "finding": finding,
                        "source_severity": (row.get("Severity") or "").strip(),
                        "recommended_action": (
                            row.get("RecommendedAction") or ""
                        ).strip(),
                    },
                    raw_reference=f"{path.name}:row-{row_number}",
                    limitations=[
                        "Imported DNS findings require service-impact validation."
                    ],
                )
            )
    return evidence
