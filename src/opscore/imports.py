from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from opscore.adapters.dns_audit import import_dns_audit_csv
from opscore.adapters.watch_run import import_watch_run
from opscore.analysis import analyze
from opscore.demo import load_bundle
from opscore.models import IncidentBundle
from opscore.reports import render_json, render_markdown


def build_imported_bundle(
    base_bundle_path: Path,
    *,
    dns_csv_path: Path,
    dns_collected_at: datetime,
    watch_run_path: Path,
    target_reference: str,
) -> IncidentBundle:
    """Build a validated bundle from base incident context and imported tool evidence."""
    base = load_bundle(base_bundle_path)
    imported = import_dns_audit_csv(
        dns_csv_path,
        collected_at=dns_collected_at,
        target_reference=target_reference,
    )
    imported.extend(import_watch_run(watch_run_path, target_reference=target_reference))
    return base.model_copy(update={"evidence": imported})


def run_import_correlation(
    base_bundle_path: Path,
    *,
    dns_csv_path: Path,
    dns_collected_at: datetime,
    watch_run_path: Path,
    target_reference: str,
    workspace: Path,
) -> tuple[Path, Path]:
    """Import evidence, correlate it, and write review-ready reports."""
    bundle = build_imported_bundle(
        base_bundle_path,
        dns_csv_path=dns_csv_path,
        dns_collected_at=dns_collected_at,
        watch_run_path=watch_run_path,
        target_reference=target_reference,
    )
    analysis_as_of = max(item.collected_at for item in bundle.evidence)
    analysis = analyze(bundle, generated_at=analysis_as_of)
    workspace.mkdir(parents=True, exist_ok=True)
    markdown_path = workspace / f"{analysis.incident.incident_id}-imported.md"
    json_path = workspace / f"{analysis.incident.incident_id}-imported.json"
    markdown_path.write_text(render_markdown(analysis), encoding="utf-8")
    json_path.write_text(render_json(analysis), encoding="utf-8")
    manifest = {
        "project": "OPSCORE",
        "workflow": "import-correlation",
        "incident_id": analysis.incident.incident_id,
        "evidence_count": len(analysis.evidence),
        "source_systems": sorted({item.source_system for item in analysis.evidence}),
        "finding_codes": [finding.code for finding in analysis.findings],
        "outputs": [markdown_path.name, json_path.name],
    }
    (workspace / "import-manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return markdown_path, json_path
