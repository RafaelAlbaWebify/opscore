from __future__ import annotations

import ipaddress
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
    public_only: bool = False
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
        if parsed.query:
            raise ValueError("collector URL must not include query parameters")
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
        data.update({"hostname": hostname, "resolved_ips": [], "error": type(exc).__name__})
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


def _http_evidence(
    request: CollectorRequest, collected_at: datetime, address: str | None
) -> EvidenceItem:
    data = _base_data(request)
    started = perf_counter()
    try:
        if address is None:
            raise ValueError("No approved resolved address")
        logical = httpx.URL(request.url)
        host = logical.host
        host_header = f"[{host}]" if ":" in host else host
        if logical.port is not None:
            host_header = f"{host_header}:{logical.port}"
        data["connected_address"] = address
        with httpx.Client(trust_env=False, follow_redirects=False) as client, client.stream(
            "GET",
            logical.copy_with(host=address),
            timeout=request.timeout_seconds,
            follow_redirects=False,
            headers={"User-Agent": "OPSCORE bounded collector", "Host": host_header},
            extensions={"sni_hostname": host},
        ) as response:
            elapsed_ms = round((perf_counter() - started) * 1000, 2)
            data.update(
                {
                    "status": response.status_code,
                    "elapsed_ms": elapsed_ms,
                    "redirect_present": "location" in response.headers,
                }
            )
        status = "completed"
        limitations = ["Response body was intentionally not downloaded."]
    except (httpx.HTTPError, ValueError) as exc:
        data.update({"status": None, "error": type(exc).__name__})
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


def _tls_evidence(
    request: CollectorRequest, collected_at: datetime, address: str | None
) -> EvidenceItem:
    parsed = urlsplit(request.url)
    hostname = parsed.hostname
    assert hostname is not None
    port = parsed.port or 443
    data = _base_data(request)
    data.update({"hostname": hostname, "port": port})
    try:
        if address is None:
            raise ValueError("No approved resolved address")
        data["connected_address"] = address
        context = ssl.create_default_context()
        with socket.create_connection((address, port), timeout=request.timeout_seconds) as raw:
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
        data.update({"error": type(exc).__name__})
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
    dns = _dns_evidence(request, collected_at)
    addresses = cast(list[str], dns.normalized_data["resolved_ips"])
    approved = bool(addresses)
    if request.public_only:
        approved = approved and all(
            ipaddress.ip_address(value).is_global
            and not ipaddress.ip_address(value).is_multicast
            for value in addresses
        )
    address = addresses[0] if approved else None
    if addresses and not approved:
        dns.limitations.append("Public-only policy rejected resolved addresses.")
    evidence = [dns, _http_evidence(request, collected_at, address)]
    if urlsplit(request.url).scheme == "https":
        evidence.append(_tls_evidence(request, collected_at, address))
    return evidence
