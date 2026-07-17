from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from opscore.models import HypothesisStatus, IncidentAnalysis, RootCauseStatus


class HypothesisAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    hypothesis_id: str = Field(pattern=r"^hyp-[a-z0-9-]+$")
    statement: str = Field(min_length=1)
    status: HypothesisStatus = HypothesisStatus.OPEN
    supporting_finding_ids: list[str] = Field(default_factory=list)
    contradicting_finding_ids: list[str] = Field(default_factory=list)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    contradicting_evidence_ids: list[str] = Field(default_factory=list)
    required_evidence: list[str] = Field(default_factory=list)
    operator_rationale: str = Field(min_length=1)


class RootCauseAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: RootCauseStatus = RootCauseStatus.UNASSESSED
    statement: str | None = None
    supporting_finding_ids: list[str] = Field(default_factory=list)
    contradicting_finding_ids: list[str] = Field(default_factory=list)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    contradicting_evidence_ids: list[str] = Field(default_factory=list)
    unresolved_required_evidence: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    operator_rationale: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_confirmation(self) -> RootCauseAssessment:
        if self.status == RootCauseStatus.CONFIRMED:
            if not self.statement:
                raise ValueError("confirmed root cause requires a statement")
            if not self.supporting_evidence_ids:
                raise ValueError("confirmed root cause requires supporting evidence")
            if self.unresolved_required_evidence:
                raise ValueError("confirmed root cause cannot retain unresolved required evidence")
        return self


class InvestigationAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    incident_id: str = Field(pattern=r"^inc-[a-z0-9-]+$")
    assessed_at: datetime
    assessed_by: str = Field(min_length=1)
    hypotheses: list[HypothesisAssessment] = Field(default_factory=list)
    root_cause: RootCauseAssessment

    @field_validator("assessed_at")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("assessment timestamp must include a timezone")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_unique_hypotheses(self) -> InvestigationAssessment:
        identifiers = [item.hypothesis_id for item in self.hypotheses]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("hypothesis identifiers must be unique")
        return self


def validate_assessment(assessment: InvestigationAssessment, analysis: IncidentAnalysis) -> None:
    if assessment.incident_id != analysis.incident.incident_id:
        raise ValueError("assessment incident does not match analysis")
    finding_ids = {item.finding_id for item in analysis.findings}
    evidence_ids = {item.evidence_id for item in analysis.evidence}
    referenced_findings: set[str] = set()
    referenced_evidence: set[str] = set()
    for hypothesis in assessment.hypotheses:
        referenced_findings.update(hypothesis.supporting_finding_ids)
        referenced_findings.update(hypothesis.contradicting_finding_ids)
        referenced_evidence.update(hypothesis.supporting_evidence_ids)
        referenced_evidence.update(hypothesis.contradicting_evidence_ids)
    root_cause = assessment.root_cause
    referenced_findings.update(root_cause.supporting_finding_ids)
    referenced_findings.update(root_cause.contradicting_finding_ids)
    referenced_evidence.update(root_cause.supporting_evidence_ids)
    referenced_evidence.update(root_cause.contradicting_evidence_ids)
    unknown_findings = referenced_findings - finding_ids
    if unknown_findings:
        raise ValueError(f"unknown finding references: {sorted(unknown_findings)}")
    unknown_evidence = referenced_evidence - evidence_ids
    if unknown_evidence:
        raise ValueError(f"unknown evidence references: {sorted(unknown_evidence)}")
