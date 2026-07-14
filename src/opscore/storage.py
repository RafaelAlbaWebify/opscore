from __future__ import annotations

import json
from pathlib import Path

from opscore.models import IncidentAnalysis, IncidentBundle
from opscore.reports import render_markdown


class IncidentStore:
    """Local JSON persistence for incident bundles and generated analyses."""

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.incidents_dir = workspace / "incidents"
        self.analyses_dir = workspace / "analyses"
        self.reports_dir = workspace / "reports"
        for directory in (self.incidents_dir, self.analyses_dir, self.reports_dir):
            directory.mkdir(parents=True, exist_ok=True)

    def _bundle_path(self, incident_id: str) -> Path:
        return self.incidents_dir / f"{incident_id}.json"

    def _analysis_path(self, incident_id: str) -> Path:
        return self.analyses_dir / f"{incident_id}.json"

    def _report_path(self, incident_id: str) -> Path:
        return self.reports_dir / f"{incident_id}.md"

    def bundle_exists(self, incident_id: str) -> bool:
        return self._bundle_path(incident_id).exists()

    def save_bundle(self, bundle: IncidentBundle) -> Path:
        path = self._bundle_path(bundle.incident.incident_id)
        path.write_text(
            json.dumps(bundle.model_dump(mode="json"), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return path

    def load_bundle(self, incident_id: str) -> IncidentBundle | None:
        path = self._bundle_path(incident_id)
        if not path.exists():
            return None
        return IncidentBundle.model_validate_json(path.read_text(encoding="utf-8"))

    def list_bundles(self) -> list[IncidentBundle]:
        return [
            IncidentBundle.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(self.incidents_dir.glob("inc-*.json"))
        ]

    def save_analysis(self, analysis: IncidentAnalysis) -> tuple[Path, Path]:
        incident_id = analysis.incident.incident_id
        analysis_path = self._analysis_path(incident_id)
        analysis_path.write_text(
            json.dumps(analysis.model_dump(mode="json"), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        report_path = self._report_path(incident_id)
        report_path.write_text(render_markdown(analysis), encoding="utf-8")
        return analysis_path, report_path

    def load_analysis(self, incident_id: str) -> IncidentAnalysis | None:
        path = self._analysis_path(incident_id)
        if not path.exists():
            return None
        return IncidentAnalysis.model_validate_json(path.read_text(encoding="utf-8"))

    def load_report(self, incident_id: str) -> str | None:
        path = self._report_path(incident_id)
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")
