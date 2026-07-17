from __future__ import annotations

import json
from pathlib import Path

from opscore.assessment import InvestigationAssessment
from opscore.history import (
    IncidentHistoryStore,
    IncidentRevision,
    IncidentRevisionMetadata,
    RevisionType,
)
from opscore.models import IncidentAnalysis, IncidentBundle
from opscore.reports import render_markdown


class IncidentStore:
    """Current JSON persistence plus append-only SQLite incident history."""

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.incidents_dir = workspace / "incidents"
        self.analyses_dir = workspace / "analyses"
        self.assessments_dir = workspace / "assessments"
        self.reports_dir = workspace / "reports"
        for directory in (
            self.incidents_dir,
            self.analyses_dir,
            self.assessments_dir,
            self.reports_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)
        self.history = IncidentHistoryStore(workspace)

    def _bundle_path(self, incident_id: str) -> Path:
        IncidentHistoryStore.validate_incident_id(incident_id)
        return self.incidents_dir / f"{incident_id}.json"

    def _analysis_path(self, incident_id: str) -> Path:
        IncidentHistoryStore.validate_incident_id(incident_id)
        return self.analyses_dir / f"{incident_id}.json"

    def _assessment_path(self, incident_id: str) -> Path:
        IncidentHistoryStore.validate_incident_id(incident_id)
        return self.assessments_dir / f"{incident_id}.json"

    def _report_path(self, incident_id: str) -> Path:
        IncidentHistoryStore.validate_incident_id(incident_id)
        return self.reports_dir / f"{incident_id}.md"

    @staticmethod
    def _write_text_atomic(path: Path, content: str) -> None:
        temporary = path.with_suffix(f"{path.suffix}.tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(path)

    def bundle_exists(self, incident_id: str) -> bool:
        return self._bundle_path(incident_id).exists()

    def save_bundle(self, bundle: IncidentBundle) -> Path:
        incident_id = bundle.incident.incident_id
        path = self._bundle_path(incident_id)
        payload = bundle.model_dump(mode="json")
        serialized = json.dumps(payload, indent=2, sort_keys=True)
        with self.history._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                self.history.append(
                    incident_id,
                    RevisionType.BUNDLE,
                    payload,
                    connection=connection,
                )
                self._write_text_atomic(path, serialized)
                connection.commit()
            except Exception:
                connection.rollback()
                raise
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
        report_path = self._report_path(incident_id)
        payload = analysis.model_dump(mode="json")
        serialized = json.dumps(payload, indent=2, sort_keys=True)
        report = render_markdown(analysis, self.load_assessment(incident_id))
        with self.history._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                self.history.append(
                    incident_id,
                    RevisionType.ANALYSIS,
                    payload,
                    connection=connection,
                )
                self._write_text_atomic(analysis_path, serialized)
                self._write_text_atomic(report_path, report)
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return analysis_path, report_path

    def load_analysis(self, incident_id: str) -> IncidentAnalysis | None:
        path = self._analysis_path(incident_id)
        if not path.exists():
            return None
        return IncidentAnalysis.model_validate_json(path.read_text(encoding="utf-8"))

    def save_assessment(self, assessment: InvestigationAssessment) -> Path:
        incident_id = assessment.incident_id
        path = self._assessment_path(incident_id)
        payload = assessment.model_dump(mode="json")
        serialized = json.dumps(payload, indent=2, sort_keys=True)
        analysis = self.load_analysis(incident_id)
        with self.history._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                self.history.append(
                    incident_id,
                    RevisionType.ASSESSMENT,
                    payload,
                    created_at=assessment.assessed_at,
                    connection=connection,
                )
                self._write_text_atomic(path, serialized)
                if analysis is not None:
                    self._write_text_atomic(
                        self._report_path(incident_id),
                        render_markdown(analysis, assessment),
                    )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return path

    def load_assessment(self, incident_id: str) -> InvestigationAssessment | None:
        path = self._assessment_path(incident_id)
        if not path.exists():
            return None
        return InvestigationAssessment.model_validate_json(path.read_text(encoding="utf-8"))

    def load_report(self, incident_id: str) -> str | None:
        path = self._report_path(incident_id)
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def list_revisions(self, incident_id: str) -> list[IncidentRevisionMetadata]:
        return self.history.list_revisions(incident_id)

    def get_revision(
        self, incident_id: str, revision_number: int
    ) -> IncidentRevision | None:
        return self.history.get_revision(incident_id, revision_number)
