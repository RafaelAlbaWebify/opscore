from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer

from opscore.demo import run_demo
from opscore.imports import run_import_correlation

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


if __name__ == "__main__":
    app()
