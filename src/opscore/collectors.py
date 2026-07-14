from __future__ import annotations

import socket
import ssl
from datetime import UTC, datetime
from time import perf_counter
from typing import Any, cast
from urllib.parse import urlsplit
from uuid import uuid4

import httpx
from pydantic import BaseModel, ConfigDict, Field, model_validator

from opscore.models import EvidenceItem


class CollectorRequest(BaseModel):
    """One explicit read-only collection target."""

    model_config = ConfigDict(extra="forbid")

    url: str = Field(min_length=1)
    target_reference: str = Field(min_length=1)
    source_location: str = Field(min_length=1)
    timeout_seconds: float = Field(default=5.0, ge=0.5, le=10.0)

    @model_validator(mode="after")
    def validate_target(self) -> CollectorRequest:
        parsed = urlsplit(self.url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("collector URL must use http or https")
        if not parsed.hostname:
            raise ValueError("collector URL must include a hostname")
        if parsed.username or parsed.password:
            raise ValueError("collector URL must not include credentials")
        if parsed.fragment:
            raise ValueError("collector URL must not include a fragment")
        try:
            port = parsed.port
        except ValueError as exc:
            raise ValueError("collector URL contains an invalid port") from exc
        if port is not None and not 1 <= port <= 65535:
            raise ValueError("collector port must be between 1 and 65535")
        return self


def _evidence_id(kind: str) -> str:
    return f"ev-live-{kind}-{uuid4().hex[:12]}"


def _base_data(request: CollectorRequest) -> dict[str, Any]:
    return {
        "requested_url": request.url,
        "source_location": request.source_location,
        "timeout_seconds": request.timeout_seconds,
    }


def _dns_evidence(request: CollectorRequest, collected_at: datetime) -> EvidenceItem:
    hostname = urlsplit(request.url).hostname
    assert hostname is not None
    data = _base_data(request)
    try:
        addresses = sorted(
            {
                item[4][0]
                for item in socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
            }
        )
        data.update({"hostname": hostname, "resolved_ips": addresses})
        status = "completed"
        limitations: list[str] = []
    except OSError as exc:
        data.update({"hostname": hostname, "resolved_ips": [], "error": str(exc)})
        status = "partial"
        limitations = ["DNS resolution failed from the recorded source location."]
    return EvidenceItem(
        evidence_id=_evidence_id("dns"),
        evidence_type="dns-resolution",
        source_system="opscore-bounded-collector",
        collected_at=collected_at,
        target_reference=request.target_reference,
        normalized_data=data,
        collection_status=status,
        limitations=limitations,
    )


def _http_evidence(request: CollectorRequest, collected_at: datetime) -> EvidenceItem:
    data = _base_data(request)
    started = perf_counter()
    try:
        with httpx.stream(
            "GET",
            request.url,
            timeout=request.timeout_seconds,
            follow_redirects=False,
            headers={"User-Agent": "OPSCORE/0.4 bounded collector"},
        ) as response:
            elapsed_ms = round((perf_counter() - started) * 1000, 2)
            data.update(
                {
                    "status": response.status_code,
                    "elapsed_ms": elapsed_ms,
                    "location": response.headers.get("location"),
                    "server": response.headers.get("server"),
                }
            )
        status = "completed"
        limitations = ["Response body was intentionally not downloaded."]
    except httpx.HTTPError as exc:
        data.update({"status": None, "error": str(exc)})
        status = "partial"
        limitations = ["HTTP reachability failed within the configured timeout."]
    return EvidenceItem(
        evidence_id=_evidence_id("http"),
        evidence_type="http-response",
        source_system="opscore-bounded-collector",
        collected_at=collected_at,
        target_reference=request.target_reference,
        normalized_data=data,
        collection_status=status,
        limitations=limitations,
    )


def _tls_evidence(request: CollectorRequest, collected_at: datetime) -> EvidenceItem:
    parsed = urlsplit(request.url)
    hostname = parsed.hostname
    assert hostname is not None
    port = parsed.port or 443
    data = _base_data(request)
    data.update({"hostname": hostname, "port": port})
    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=request.timeout_seconds) as raw:
            with context.wrap_socket(raw, server_hostname=hostname) as secured:
                certificate = cast(dict[str, Any], secured.getpeercert() or {})
        expires_raw = certificate.get("notAfter")
        expires_at = (
            datetime.fromtimestamp(ssl.cert_time_to_seconds(expires_raw), tz=UTC)
            if isinstance(expires_raw, str)
            else None
        )
        days_remaining = (
            int((expires_at - collected_at).total_seconds() // 86400)
            if expires_at is not None
            else None
        )
        subject_alt_names = [
            value
            for kind, value in certificate.get("subjectAltName", [])
            if kind == "DNS"
        ]
        data.update(
            {
                "expires_at": expires_at.isoformat() if expires_at else None,
                "days_remaining": days_remaining,
                "subject_alt_names": subject_alt_names,
            }
        )
        status = "completed"
        limitations: list[str] = []
    except (OSError, ssl.SSLError, ValueError) as exc:
        data.update({"error": str(exc)})
        status = "partial"
        limitations = ["TLS evidence could not be collected within the configured boundary."]
    return EvidenceItem(
        evidence_id=_evidence_id("tls"),
        evidence_type="tls-certificate",
        source_system="opscore-bounded-collector",
        collected_at=collected_at,
        target_reference=request.target_reference,
        normalized_data=data,
        collection_status=status,
        limitations=limitations,
    )


def collect_target(request: CollectorRequest) -> list[EvidenceItem]:
    """Collect DNS and HTTP evidence, plus TLS evidence for HTTPS targets."""

    collected_at = datetime.now(UTC)
    evidence = [
        _dns_evidence(request, collected_at),
        _http_evidence(request, collected_at),
    ]
    if urlsplit(request.url).scheme == "https":
        evidence.append(_tls_evidence(request, collected_at))
    return evidence
