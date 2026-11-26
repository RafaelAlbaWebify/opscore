from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from opscore.models import Confidence, EvidenceItem, Finding, FindingSeverity

MAX_IMPORT_BYTES = 2 * 1024 * 1024
MAX_RECORDS = 10000


class OperationalImport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["application-log", "windows-event", "iis"]
    target_reference: str = Field(min_length=1)
    collected_at: datetime
    content: str = Field(repr=False)


LABELS = {
    "APP_HTTP_5XX": "HTTP server error responses",
    "APP_AUTH_FAILURE": "HTTP authentication or authorization responses",
    "APP_TIMEOUT": "Timeout signals",
    "APP_DNS": "DNS resolution error signals",
    "APP_TLS": "TLS certificate or handshake error signals",
    "APP_DATABASE": "Database dependency error signals",
    "APP_EXCEPTION": "Exception signals",
    "WIN_SERVICE_FAILURE": "Service Control Manager failure events",
    "WIN_FAILED_LOGON": "Security failed logon events",
    "WIN_APPLICATION_ERROR": "Application error events",
    "WIN_DNS_ERROR": "DNS Client error events",
    "WIN_REBOOT": "System restart or shutdown events",
    "IIS_SERVICE_STOPPED": "Stopped IIS service observations",
    "IIS_SITE_STOPPED": "Stopped IIS site observations",
    "IIS_POOL_STOPPED": "Stopped IIS application pool observations",
}


def _text(record: dict[str, Any], key: str) -> str:
    value = record.get(key)
    return value.casefold() if isinstance(value, str) else ""


def _records(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) > MAX_RECORDS:
        raise ValueError("Expected a bounded JSON record array")
    if not all(isinstance(record, dict) for record in value):
        raise ValueError("Each record must be a JSON object")
    return value


def _app(record: dict[str, Any]) -> list[str]:
    codes: list[str] = []
    status = record.get("status_code")
    if type(status) is int and 500 <= status <= 599:
        codes.append("APP_HTTP_5XX")
    if type(status) is int and status in (401, 403):
        codes.append("APP_AUTH_FAILURE")
    message = _text(record, "raw") + " " + _text(record, "message")
    patterns = {
        "APP_TIMEOUT": ("timed out", "timeout", "deadline exceeded"),
        "APP_DNS": ("name resolution failed", "dns resolution failed", "nxdomain"),
        "APP_TLS": ("certificate verify failed", "tls handshake failed", "certificate expired"),
        "APP_DATABASE": ("database connection failed", "sql connection failed", "deadlock"),
        "APP_EXCEPTION": ("traceback", "unhandled exception"),
    }
    for code, terms in patterns.items():
        if any(term in message for term in terms):
            codes.append(code)
    return codes


def _windows(record: dict[str, Any]) -> list[str]:
    event_id = record.get("event_id")
    if type(event_id) is not int:
        return []
    provider = _text(record, "provider")
    channel = _text(record, "log_name")
    if provider == "service control manager" and event_id in {
        7000, 7009, 7011, 7022, 7023, 7024, 7026, 7031, 7034, 7043
    }:
        return ["WIN_SERVICE_FAILURE"]
    if event_id == 4625 and ("security-auditing" in provider or channel == "security"):
        return ["WIN_FAILED_LOGON"]
    if event_id in {1000, 1001, 1026} and provider in {
        "application error", ".net runtime", "windows error reporting"
    }:
        return ["WIN_APPLICATION_ERROR"]
    if event_id == 1014 and (
        "dns-client" in provider or "dns client" in provider or "dns-client" in channel
    ):
        return ["WIN_DNS_ERROR"]
    if event_id in {12, 41, 1074, 6005, 6006, 6008} and provider in {
        "user32", "eventlog", "microsoft-windows-kernel-power",
        "microsoft-windows-kernel-general"
    }:
        return ["WIN_REBOOT"]
    return []


def normalize_import(request: OperationalImport) -> EvidenceItem:
    try:
        data = request.content.encode("utf-8")
        if not data or len(data) > MAX_IMPORT_BYTES:
            raise ValueError("Import must contain at most 2 MiB")
        payload = json.loads(data)
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise ValueError("Invalid JSON import") from None
    counts: Counter[str] = Counter()
    positions: dict[str, list[int]] = {}
    total = 0
    groups: list[tuple[str, list[dict[str, Any]]]] = []
    if request.kind == "iis":
        if not isinstance(payload, dict):
            raise ValueError("Expected an IIS JSON object")
        for key in ("services", "sites", "application_pools"):
            groups.append((key, _records(payload.get(key, []))))
    else:
        if isinstance(payload, dict):
            key = "entries" if request.kind == "application-log" else "events"
            payload = payload.get(key)
        groups.append((request.kind, _records(payload)))
    for group, records in groups:
        total += len(records)
        if total > MAX_RECORDS:
            raise ValueError("Too many records")
        for index, record in enumerate(records, start=1):
            codes: list[str] = []
            if group == "application-log":
                codes = _app(record)
            elif group == "windows-event":
                codes = _windows(record)
            elif group == "services":
                if _text(record, "name") in {"w3svc", "was"}:
                    if _text(record, "status") == "stopped":
                        codes = ["IIS_SERVICE_STOPPED"]
            elif _text(record, "state") == "stopped":
                codes = ["IIS_SITE_STOPPED" if group == "sites" else "IIS_POOL_STOPPED"]
            for code in codes:
                counts[code] += 1
                if len(positions.setdefault(code, [])) < 10:
                    positions[code].append(index)
    digest = hashlib.sha256(data).hexdigest()
    identity = hashlib.sha256(
        f"{request.kind}:{request.target_reference}:{digest}".encode()
    ).hexdigest()
    return EvidenceItem(
        evidence_id=f"ev-operational-{identity}",
        evidence_type=f"operational-{request.kind}",
        source_system="opscore-operational-import",
        collected_at=request.collected_at,
        target_reference=request.target_reference,
        normalized_data={
            "record_count": total,
            "signal_counts": dict(counts),
            "sample_record_positions": positions,
            "source_sha256": digest,
        },
        limitations=[
            "Only selected diagnostic signals and record positions retained.",
            "Collection time is operator supplied; event times are not correlated.",
            "No signal does not establish service health or absence of errors.",
        ],
    )


def operational_findings(evidence: list[EvidenceItem]) -> list[Finding]:
    findings: list[Finding] = []
    for item in evidence:
        if item.source_system != "opscore-operational-import":
            continue
        counts = item.normalized_data.get("signal_counts")
        if not isinstance(counts, dict):
            continue
        for code, count in sorted(counts.items()):
            if code not in LABELS or type(count) is not int or count <= 0:
                continue
            findings.append(
                Finding(
                    finding_id=f"finding-{code.lower().replace('_', '-')}-{item.evidence_id}",
                    code=code,
                    statement=f"{LABELS[code]}: {count}.",
                    severity=FindingSeverity.WARNING,
                    confidence=Confidence.MEDIUM,
                    supporting_evidence_ids=[item.evidence_id],
                    missing_evidence=["Original record context and incident time window"],
                    safe_next_checks=["Review the authorized original records and service state."],
                    non_actions=["Do not infer confirmed root cause or restart services."],
                )
            )
    return findings
