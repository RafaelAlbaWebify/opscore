from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer

from opscore.collectors import CollectorRequest, collect_target
from opscore.connectivity import TcpConnectivityRequest, collect_tcp_connectivity
from opscore.demo import run_demo
from opscore.imports import run_import_correlation
from opscore.storage import IncidentStore
from opscore.watch_handoff import WatchHandoff, evidence_from_handoff

app = typer.Typer(help="OPSCORE infrastructure incident evidence workbench")
_DEFAULT_DNS_COLLECTED_AT = datetime.fromisoformat("2026-07-14T08:08:00+00:00")


@app.callback()
def main() -> None:
    """OPSCORE command group."""


@app.command()
def demo(
    workspace: Annotated[Path, typer.Option(help="Output workspace")] = Path(".opscore-data"),
    sample: Annotated[Path, typer.Option(help="Incident bundle JSON")] = Path(
        "samples/incidents/orders-service-unavailable.json"
    ),
) -> None:
    markdown_path, json_path = run_demo(sample, workspace)
    typer.echo("OPSCORE demo PASS")
    typer.echo(f"Markdown: {markdown_path}")
    typer.echo(f"JSON: {json_path}")


@app.command()
def correlate(
    workspace: Annotated[Path, typer.Option(help="Output workspace")] = Path(
        ".opscore-data/imported"
    ),
    base_bundle: Annotated[Path, typer.Option(help="Incident and service context JSON")] = Path(
        "samples/incidents/orders-service-unavailable.json"
    ),
    dns_csv: Annotated[Path, typer.Option(help="DNS Audit Tool CSV export")] = Path(
        "samples/imports/dns-audit-sample.csv"
    ),
    dns_collected_at: Annotated[
        datetime, typer.Option(help="Timezone-aware DNS audit collection time")
    ] = _DEFAULT_DNS_COLLECTED_AT,
    watch_run: Annotated[Path, typer.Option(help="WATCH JSON run export")] = Path(
        "samples/imports/watch-run-sample.json"
    ),
    target_reference: Annotated[
        str, typer.Option(help="OPSCORE service ID associated with imported evidence")
    ] = "orders-web",
) -> None:
    markdown_path, json_path = run_import_correlation(
        base_bundle,
        dns_csv_path=dns_csv,
        dns_collected_at=dns_collected_at,
        watch_run_path=watch_run,
        target_reference=target_reference,
        workspace=workspace,
    )
    typer.echo("OPSCORE import correlation PASS")
    typer.echo(f"Markdown: {markdown_path}")
    typer.echo(f"JSON: {json_path}")


@app.command()
def collect(
    url: Annotated[str, typer.Option(help="One explicit HTTP or HTTPS target")],
    target_reference: Annotated[str, typer.Option(help="Incident service ID")],
    source_location: Annotated[str, typer.Option(help="Operator-defined collection location")],
    timeout_seconds: Annotated[
        float, typer.Option(min=0.5, max=10.0, help="Per-operation timeout")
    ] = 5.0,
    workspace: Annotated[Path, typer.Option(help="Output workspace")] = Path(
        ".opscore-data/collected"
    ),
) -> None:
    request = CollectorRequest(
        url=url,
        target_reference=target_reference,
        source_location=source_location,
        timeout_seconds=timeout_seconds,
    )
    evidence = collect_target(request)
    workspace.mkdir(parents=True, exist_ok=True)
    output = workspace / "bounded-evidence.json"
    output.write_text(
        json.dumps([item.model_dump(mode="json") for item in evidence], indent=2),
        encoding="utf-8",
    )
    typer.echo("OPSCORE bounded collection PASS")
    typer.echo(f"Evidence: {output}")


@app.command("connectivity")
def connectivity(
    host: Annotated[str, typer.Option(help="One explicit hostname or IP address")],
    port: Annotated[int, typer.Option(min=1, max=65535, help="One explicit TCP port")],
    target_reference: Annotated[str, typer.Option(help="Incident service ID")],
    source_location: Annotated[str, typer.Option(help="Operator-defined source location")],
    timeout_seconds: Annotated[
        float, typer.Option(min=0.5, max=10.0, help="Connection timeout")
    ] = 3.0,
    workspace: Annotated[Path, typer.Option(help="Output workspace")] = Path(
        ".opscore-data/connectivity"
    ),
) -> None:
    evidence = collect_tcp_connectivity(
        TcpConnectivityRequest(
            host=host,
            port=port,
            target_reference=target_reference,
            source_location=source_location,
            timeout_seconds=timeout_seconds,
        )
    )
    workspace.mkdir(parents=True, exist_ok=True)
    output = workspace / "tcp-connectivity-evidence.json"
    output.write_text(
        json.dumps(evidence.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )
    typer.echo("OPSCORE bounded TCP connectivity PASS")
    typer.echo(f"Evidence: {output}")


@app.command("watch-handoff")
def validate_watch_handoff(
    handoff_file: Annotated[Path, typer.Option(help="WATCH handoff JSON file")] = Path(
        "samples/imports/watch-handoff-v1.json"
    ),
    workspace: Annotated[Path, typer.Option(help="Output workspace")] = Path(
        ".opscore-data/watch-handoff"
    ),
) -> None:
    payload = json.loads(handoff_file.read_text(encoding="utf-8"))
    handoff = WatchHandoff.model_validate(payload)
    evidence = evidence_from_handoff(handoff)
    workspace.mkdir(parents=True, exist_ok=True)
    output = workspace / f"{handoff.run.run_id}-evidence.json"
    output.write_text(
        json.dumps([item.model_dump(mode="json") for item in evidence], indent=2),
        encoding="utf-8",
    )
    typer.echo("OPSCORE WATCH handoff PASS")
    typer.echo(f"Contract: {handoff.contract_version}")
    typer.echo(f"Evidence: {output}")


@app.command("history")
def history(
    incident_id: Annotated[str, typer.Argument(help="Incident identifier")],
    workspace: Annotated[Path, typer.Option(help="OPSCORE workspace")] = Path(
        ".opscore-data/api"
    ),
    revision: Annotated[
        int | None,
        typer.Option(min=1, help="Optional revision number to retrieve"),
    ] = None,
) -> None:
    """Show read-only immutable incident revision history as JSON."""
    store = IncidentStore(workspace)
    try:
        if revision is None:
            payload = [
                item.model_dump(mode="json")
                for item in store.list_revisions(incident_id)
            ]
        else:
            item = store.get_revision(incident_id, revision)
            if item is None:
                raise typer.BadParameter("revision not found", param_hint="--revision")
            payload = item.model_dump(mode="json")
    except ValueError as exc:
        raise typer.BadParameter(str(exc), param_hint="incident_id") from exc
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    app()
