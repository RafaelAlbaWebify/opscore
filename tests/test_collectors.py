from __future__ import annotations

import json
import socket
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from opscore.cli import app as cli_app
from opscore.collectors import CollectorRequest, collect_target


def test_collector_request_rejects_unsafe_targets() -> None:
    invalid_urls = [
        "ftp://example.test",
        "https://user:secret@example.test",
        "https://example.test/path#fragment",
        "https://example.test:99999",
    ]
    for url in invalid_urls:
        with pytest.raises(ValidationError):
            CollectorRequest(
                url=url,
                target_reference="orders-web",
                source_location="test-runner",
            )


def test_http_target_collects_failure_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_dns(*args: object, **kwargs: object) -> object:
        raise socket.gaierror("synthetic DNS failure")

    def fail_http(*args: object, **kwargs: object) -> object:
        request = httpx.Request("GET", "http://example.test")
        raise httpx.ConnectError("synthetic HTTP failure", request=request)

    monkeypatch.setattr(socket, "getaddrinfo", fail_dns)
    monkeypatch.setattr(httpx, "stream", fail_http)

    evidence = collect_target(
        CollectorRequest(
            url="http://example.test",
            target_reference="orders-web",
            source_location="pytest",
            timeout_seconds=1,
        )
    )

    assert [item.evidence_type for item in evidence] == ["dns-resolution", "http-response"]
    assert all(item.collection_status == "partial" for item in evidence)
    assert all(item.normalized_data["source_location"] == "pytest" for item in evidence)


def test_https_target_adds_tls_failure_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def synthetic_dns(*args: object, **kwargs: object) -> list[tuple[object, ...]]:
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                6,
                "",
                ("192.0.2.10", 0),
            )
        ]

    def fail_http(*args: object, **kwargs: object) -> object:
        request = httpx.Request("GET", "https://example.test")
        raise httpx.ConnectError("synthetic HTTP failure", request=request)

    def fail_tls(*args: object, **kwargs: object) -> object:
        raise TimeoutError("synthetic TLS timeout")

    monkeypatch.setattr(socket, "getaddrinfo", synthetic_dns)
    monkeypatch.setattr(httpx, "stream", fail_http)
    monkeypatch.setattr(socket, "create_connection", fail_tls)

    evidence = collect_target(
        CollectorRequest(
            url="https://example.test",
            target_reference="orders-web",
            source_location="pytest",
            timeout_seconds=1,
        )
    )

    assert [item.evidence_type for item in evidence] == [
        "dns-resolution",
        "http-response",
        "tls-certificate",
    ]
    assert evidence[0].normalized_data["resolved_ips"] == ["192.0.2.10"]
    assert evidence[2].collection_status == "partial"
    assert "synthetic TLS timeout" in evidence[2].normalized_data["error"]


def test_collect_cli_writes_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "opscore.cli.collect_target",
        lambda request: [
            collect_target(
                CollectorRequest(
                    url="http://example.test",
                    target_reference="orders-web",
                    source_location="pytest",
                    timeout_seconds=1,
                )
            )[0]
        ],
    )
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.0.2.10", 0))
        ],
    )

    result = CliRunner().invoke(
        cli_app,
        [
            "collect",
            "--url",
            "http://example.test",
            "--target-reference",
            "orders-web",
            "--source-location",
            "pytest",
            "--workspace",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    output = tmp_path / "bounded-evidence.json"
    assert output.exists()
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload[0]["evidence_type"] == "dns-resolution"
