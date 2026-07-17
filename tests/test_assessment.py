from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from opscore.analysis import analyze
from opscore.assessment import (
    HypothesisAssessment,
    InvestigationAssessment,
    RootCauseAssessment,
    validate_assessment,
)
from opscore.demo import load_bundle
from opscore.models import HypothesisStatus, RootCauseStatus

SAMPLE = Path("samples/incidents/orders-service-unavailable.json")


def test_assessment_accepts_known_references() -> None:
    analysis = analyze(load_bundle(SAMPLE))
    finding = analysis.findings[0]
    evidence_id = finding.supporting_evidence_ids[0]
    assessment = InvestigationAssessment(
        incident_id=analysis.incident.incident_id,
        assessed_at=datetime(2026, 7, 17, 16, 0, tzinfo=UTC),
        assessed_by="operator",
        hypotheses=[
            HypothesisAssessment(
                hypothesis_id="hyp-application-path",
                statement="Application path is unavailable after DNS resolution.",
                status=HypothesisStatus.SUPPORTED,
                supporting_finding_ids=[finding.finding_id],
                supporting_evidence_ids=[evidence_id],
                operator_rationale="The evidence supports continued investigation.",
            )
        ],
        root_cause=RootCauseAssessment(
            status=RootCauseStatus.SUSPECTED,
            statement="Application-layer availability failure.",
            supporting_finding_ids=[finding.finding_id],
            supporting_evidence_ids=[evidence_id],
            unresolved_required_evidence=["server-side service state"],
            operator_rationale="Server evidence is still missing.",
        ),
    )
    validate_assessment(assessment, analysis)


def test_assessment_rejects_unknown_evidence() -> None:
    analysis = analyze(load_bundle(SAMPLE))
    assessment = InvestigationAssessment(
        incident_id=analysis.incident.incident_id,
        assessed_at=datetime(2026, 7, 17, 16, 0, tzinfo=UTC),
        assessed_by="operator",
        root_cause=RootCauseAssessment(
            status=RootCauseStatus.SUPPORTED,
            statement="Candidate cause.",
            supporting_evidence_ids=["ev-unknown"],
            operator_rationale="Manual assessment.",
        ),
    )
    with pytest.raises(ValueError, match="unknown evidence references"):
        validate_assessment(assessment, analysis)


def test_confirmed_root_cause_requires_evidence() -> None:
    with pytest.raises(ValidationError, match="supporting evidence"):
        RootCauseAssessment(
            status=RootCauseStatus.CONFIRMED,
            statement="Confirmed cause.",
            operator_rationale="Manual confirmation.",
        )


def test_confirmed_root_cause_rejects_unresolved_gaps() -> None:
    with pytest.raises(ValidationError, match="unresolved required evidence"):
        RootCauseAssessment(
            status=RootCauseStatus.CONFIRMED,
            statement="Confirmed cause.",
            supporting_evidence_ids=["ev-example"],
            unresolved_required_evidence=["service logs"],
            operator_rationale="Manual confirmation.",
        )


def test_assessment_requires_timezone() -> None:
    with pytest.raises(ValidationError):
        InvestigationAssessment(
            incident_id="inc-example",
            assessed_at=datetime(2026, 7, 17, 16, 0),
            assessed_by="operator",
            root_cause=RootCauseAssessment(operator_rationale="Not assessed."),
        )
