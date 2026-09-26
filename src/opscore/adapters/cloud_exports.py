from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from opscore.models import EvidenceItem


def _load_records(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = [payload]
    if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
        raise ValueError("cloud export must be a JSON object or list of JSON objects")
    return payload


def _parse_collected_at(record: dict[str, Any]) -> datetime:
    raw = record.get("collectedAt") or record.get("timestamp")
    if raw is None:
        raise ValueError("cloud export record requires collectedAt or timestamp")
    value = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("cloud export timestamp must include timezone")
    return value.astimezone(UTC)


def import_azure_vm_export(path: Path, *, target_reference: str) -> list[EvidenceItem]:
    evidence: list[EvidenceItem] = []
    for index, record in enumerate(_load_records(path), start=1):
        name = str(record.get("vmName") or record.get("resourceId") or f"azure-{index}")
        normalized = {
            "provider": "azure",
            "resource_name": name,
            "power_state": record.get("powerState"),
            "resource_health": record.get("resourceHealth"),
            "network_reachability": record.get("networkReachability"),
            "cpu_percent": record.get("cpuPercent"),
            "disk_free_percent": record.get("diskFreePercent"),
        }
        evidence.append(
            EvidenceItem(
                evidence_id=f"ev-azure-{index}",
                evidence_type="cloud-vm-state",
                source_system="azure-export",
                collected_at=_parse_collected_at(record),
                target_reference=target_reference,
                normalized_data=normalized,
                raw_reference=path.name,
                limitations=[
                    "Imported export only; no live Azure API or tenant connection.",
                    "Resource Health and workload symptoms require contextual validation.",
                ],
            )
        )
    return evidence


def import_aws_ec2_export(path: Path, *, target_reference: str) -> list[EvidenceItem]:
    evidence: list[EvidenceItem] = []
    for index, record in enumerate(_load_records(path), start=1):
        name = str(record.get("instanceId") or record.get("name") or f"aws-{index}")
        normalized = {
            "provider": "aws",
            "resource_name": name,
            "instance_state": record.get("state"),
            "status_check": record.get("statusCheck"),
            "network_reachability": record.get("networkReachability"),
            "cpu_percent": record.get("cpuPercent"),
            "disk_free_percent": record.get("diskFreePercent"),
        }
        evidence.append(
            EvidenceItem(
                evidence_id=f"ev-aws-{index}",
                evidence_type="cloud-instance-state",
                source_system="aws-export",
                collected_at=_parse_collected_at(record),
                target_reference=target_reference,
                normalized_data=normalized,
                raw_reference=path.name,
                limitations=[
                    "Imported export only; no live AWS API or account connection.",
                    "Status checks and workload symptoms require contextual validation.",
                ],
            )
        )
    return evidence
