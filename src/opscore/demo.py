from __future__ import annotations

import json
from pathlib import Path

from opscore.analysis import analyze
from opscore.models import IncidentBundle
from opscore.reports import render_json, render_markdown


def load_bundle(path: Path) -> IncidentBundle:
    return IncidentBundle.model_validate_json(path.read_text(encoding="utf-8"))


def run_demo(sample_path: Path, workspace: Path) -> tuple[Path, Path]:
    workspace.mkdir(parents=True, exist_ok=True)
    bundle = load_bundle(sample_path)
    analysis_as_of = max(
        (item.collected_at for item in bundle.evidence),
        default=bundle.incident.investigation_started_at,
    )
    analysis = analyze(bundle, generated_at=analysis_as_of)
    markdown_path = workspace / f"{analysis.incident.incident_id}.md"
    json_path = workspace / f"{analysis.incident.incident_id}.json"
    markdown_path.write_text(render_markdown(analysis), encoding="utf-8")
    json_path.write_text(render_json(analysis), encoding="utf-8")
    manifest = {
        "project": "OPSCORE",
        "incident_id": analysis.incident.incident_id,
        "evidence_count": len(analysis.evidence),
        "finding_codes": [finding.code for finding in analysis.findings],
        "outputs": [markdown_path.name, json_path.name],
    }
    (workspace / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return markdown_path, json_path
