from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response, status
from fastapi.responses import HTMLResponse

from opscore import __version__
from opscore.analysis import analyze
from opscore.models import EvidenceItem, Incident, IncidentAnalysis, IncidentBundle
from opscore.storage import IncidentStore
from opscore.ui import render_operator_interface


def create_app(workspace: Path | None = None) -> FastAPI:
    resolved_workspace = workspace or Path(
        os.environ.get("OPSCORE_WORKSPACE", ".opscore-data/api")
    )
    store = IncidentStore(resolved_workspace)
    application = FastAPI(title="OPSCORE API", version=__version__)

    @application.get("/", response_class=HTMLResponse, include_in_schema=False)
    def operator_interface() -> str:
        return render_operator_interface()

    @application.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "opscore", "version": __version__}

    @application.get("/api/incidents", response_model=list[Incident])
    def list_incidents() -> list[Incident]:
        return [bundle.incident for bundle in store.list_bundles()]

    @application.post(
        "/api/incidents",
        response_model=IncidentBundle,
        status_code=status.HTTP_201_CREATED,
    )
    def create_incident(bundle: IncidentBundle) -> IncidentBundle:
        incident_id = bundle.incident.incident_id
        if store.bundle_exists(incident_id):
            raise HTTPException(status_code=409, detail="incident already exists")
        store.save_bundle(bundle)
        return bundle

    @application.get("/api/incidents/{incident_id}", response_model=IncidentBundle)
    def get_incident(incident_id: str) -> IncidentBundle:
        bundle = store.load_bundle(incident_id)
        if bundle is None:
            raise HTTPException(status_code=404, detail="incident not found")
        return bundle

    @application.post(
        "/api/incidents/{incident_id}/evidence",
        response_model=IncidentBundle,
        status_code=status.HTTP_201_CREATED,
    )
    def add_evidence(incident_id: str, evidence: EvidenceItem) -> IncidentBundle:
        bundle = store.load_bundle(incident_id)
        if bundle is None:
            raise HTTPException(status_code=404, detail="incident not found")
        if any(item.evidence_id == evidence.evidence_id for item in bundle.evidence):
            raise HTTPException(status_code=409, detail="evidence already exists")
        updated = bundle.model_copy(update={"evidence": [*bundle.evidence, evidence]})
        store.save_bundle(updated)
        return updated

    @application.post(
        "/api/incidents/{incident_id}/analyze",
        response_model=IncidentAnalysis,
    )
    def analyze_incident(incident_id: str) -> IncidentAnalysis:
        bundle = store.load_bundle(incident_id)
        if bundle is None:
            raise HTTPException(status_code=404, detail="incident not found")
        generated_at = max(
            (item.collected_at for item in bundle.evidence),
            default=datetime.now(UTC),
        )
        analysis = analyze(bundle, generated_at=generated_at)
        store.save_analysis(analysis)
        return analysis

    @application.get(
        "/api/incidents/{incident_id}/analysis",
        response_model=IncidentAnalysis,
    )
    def get_analysis(incident_id: str) -> IncidentAnalysis:
        analysis = store.load_analysis(incident_id)
        if analysis is None:
            raise HTTPException(status_code=404, detail="analysis not found")
        return analysis

    @application.get("/api/incidents/{incident_id}/report.md")
    def get_report(incident_id: str) -> Response:
        report = store.load_report(incident_id)
        if report is None:
            raise HTTPException(status_code=404, detail="report not found")
        return Response(content=report, media_type="text/markdown; charset=utf-8")

    return application


app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run("opscore.api:app", host="127.0.0.1", port=8000)
