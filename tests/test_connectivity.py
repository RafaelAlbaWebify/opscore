from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from opscore.api import create_app
from opscore.connectivity import TcpConnectivityRequest, collect_tcp_connectivity
from opscore.demo import load_bundle

SAMPLE = Path("samples/incidents/orders-service-unavailable.json")


class SyntheticSocket:
    def __enter__(self) -> SyntheticSocket:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def test_request_rejects_url_path_and_target_list() -> None:
    base = {
        "port": 443,
        "target_reference": "orders-web",
        "source_location": "pytest",
    }
    for host in ["https://orders.example.test", "orders.example.test/path", "a,b"]:
        with pytest.raises(ValidationError):
            TcpConnectivityRequest(host=host, **base)


def test_successful_connectivity_is_traceable(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[tuple[str, int], float]] = []

    def synthetic_connection(
        address: tuple[str, int], timeout: float
    ) -> SyntheticSocket:
        calls.append((address, timeout))
        return SyntheticSocket()

    monkeypatch.setattr("opscore.connectivity.socket.create_connection", synthetic_connection)
    request = TcpConnectivityRequest(
        host="orders.example.test",
        port=443,
        target_reference="orders-web",
        source_location="pytest",
        timeout_seconds=2,
    )
    evidence = collect_tcp_connectivity(request)

    assert calls == [(('orders.example.test', 443), 2.0)]
    assert evidence.evidence_type == "tcp-connectivity"
    assert evidence.normalized_data["connected"] is True
    assert evidence.normalized_data["host"] == "orders.example.test"
    assert evidence.collection_status == "completed"


def test_failed_connectivity_is_partial(monkeypatch: pytest.MonkeyPatch) -> None:
    def failed_connection(address: tuple[str, int], timeout: float) -> None:
        raise TimeoutError("synthetic timeout")

    monkeypatch.setattr("opscore.connectivity.socket.create_connection", failed_connection)
    evidence = collect_tcp_connectivity(
        TcpConnectivityRequest(
            host="orders.example.test",
            port=443,
            target_reference="orders-web",
            source_location="pytest",
        )
    )

    assert evidence.normalized_data["connected"] is False
    assert evidence.collection_status == "partial"
    assert "synthetic timeout" in evidence.normalized_data["error"]


def test_connectivity_api_lifecycle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "opscore.connectivity.socket.create_connection",
        lambda address, timeout: SyntheticSocket(),
    )
    client = TestClient(create_app(tmp_path))
    bundle = load_bundle(SAMPLE).model_dump(mode="json")
    assert client.post("/api/incidents", json=bundle).status_code == 201

    payload = {
        "host": "orders.example.test",
        "port": 443,
        "target_reference": "orders-web",
        "source_location": "pytest",
        "timeout_seconds": 2,
    }
    response = client.post(
        "/api/incidents/inc-orders-001/connectivity",
        json=payload,
    )
    assert response.status_code == 201
    assert response.json()["evidence"][-1]["evidence_type"] == "tcp-connectivity"

    payload["target_reference"] = "unknown-service"
    rejected = client.post(
        "/api/incidents/inc-orders-001/connectivity",
        json=payload,
    )
    assert rejected.status_code == 422
