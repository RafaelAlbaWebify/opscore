from __future__ import annotations

import socket
from datetime import UTC, datetime
from time import perf_counter
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from opscore.models import EvidenceItem


class TcpConnectivityRequest(BaseModel):
    """One explicit read-only TCP connection attempt."""

    model_config = ConfigDict(extra="forbid")

    host: str = Field(min_length=1, max_length=253)
    port: int = Field(ge=1, le=65535)
    target_reference: str = Field(min_length=1)
    source_location: str = Field(min_length=1)
    timeout_seconds: float = Field(default=3.0, ge=0.5, le=10.0)

    @field_validator("host")
    @classmethod
    def validate_host(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized or any(char.isspace() for char in normalized):
            raise ValueError("TCP host must be one hostname or IP address")
        if "://" in normalized or "/" in normalized or "," in normalized:
            raise ValueError("TCP host must not contain a URL, path or target list")
        return normalized


def collect_tcp_connectivity(request: TcpConnectivityRequest) -> EvidenceItem:
    """Attempt one TCP connection without sending application data."""

    collected_at = datetime.now(UTC)
    started = perf_counter()
    data: dict[str, Any] = {
        "host": request.host,
        "port": request.port,
        "source_location": request.source_location,
        "timeout_seconds": request.timeout_seconds,
    }

    try:
        with socket.create_connection(
            (request.host, request.port),
            timeout=request.timeout_seconds,
        ):
            elapsed_ms = round((perf_counter() - started) * 1000, 2)
        data.update({"connected": True, "elapsed_ms": elapsed_ms, "error": None})
        status = "completed"
        limitations = [
            "A successful TCP handshake does not prove application health or authentication."
        ]
    except OSError as exc:
        elapsed_ms = round((perf_counter() - started) * 1000, 2)
        data.update({"connected": False, "elapsed_ms": elapsed_ms, "error": str(exc)})
        status = "partial"
        limitations = [
            "The connection failed from the recorded source location within the timeout."
        ]

    return EvidenceItem(
        evidence_id=f"ev-live-tcp-{uuid4().hex[:12]}",
        evidence_type="tcp-connectivity",
        source_system="opscore-bounded-connectivity",
        collected_at=collected_at,
        target_reference=request.target_reference,
        normalized_data=data,
        collection_status=status,
        limitations=limitations,
    )
