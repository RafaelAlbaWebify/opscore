from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class IncidentSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(StrEnum):
    NEW = "new"
    COLLECTING_EVIDENCE = "collecting-evidence"
    ANALYZING = "analyzing"
    AWAITING_EVIDENCE = "awaiting-evidence"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Confidence(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FindingSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class HypothesisStatus(StrEnum):
    OPEN = "open"
    SUPPORTED = "supported"
    WEAKENED = "weakened"
    DISPROVEN = "disproven"
    CONFIRMED = "confirmed"


class RootCauseStatus(StrEnum):
    UNASSESSED = "unassessed"
    SUSPECTED = "suspected"
    SUPPORTED = "supported"
    CONFIRMED = "confirmed"
    DISPROVEN = "disproven"


class Service(BaseModel):
    model_config = ConfigDict(extra="forbid")
    service_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    name: str = Field(min_length=1)
    environment: str = Field(min_length=1)
    service_type: str = Field(min_length=1)
    expected_endpoints: list[str] = Field(default_factory=list)
    owner: str | None = None
    criticality: IncidentSeverity = IncidentSeverity.MEDIUM


class Dependency(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dependency_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    source_service_id: str
    target_service_id: str
    dependency_type: str
    required: bool = True
    evidence_source: str = "declared"
    confidence: Confidence = Confidence.MEDIUM


class Incident(BaseModel):
    model_config = ConfigDict(extra="forbid")
    incident_id: str = Field(pattern=r"^inc-[a-z0-9-]+$")
    title: str = Field(min_length=1)
    reported_symptom: str = Field(min_length=1)
    environment: str = Field(min_length=1)
    reported_at: datetime
    investigation_started_at: datetime
    affected_service_ids: list[str] = Field(min_length=1)
    severity: IncidentSeverity
    status: IncidentStatus = IncidentStatus.NEW
    root_cause_status: RootCauseStatus = RootCauseStatus.UNASSESSED

    @field_validator("reported_at", "investigation_started_at")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("incident timestamps must include a timezone")
        return value.astimezone(UTC)


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evidence_id: str = Field(pattern=r"^ev-[a-z0-9-]+$")
    evidence_type: str
    source_system: str
    collected_at: datetime
    target_reference: str
    normalized_data: dict[str, Any] = Field(default_factory=dict)
    raw_reference: str | None = None
    collection_status: str = "completed"
    limitations: list[str] = Field(default_factory=list)

    @field_validator("collected_at")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("evidence timestamp must include a timezone")
        return value.astimezone(UTC)


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    finding_id: str
    code: str
    statement: str
    severity: FindingSeverity
    confidence: Confidence
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    contradictory_evidence_ids: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    safe_next_checks: list[str] = Field(default_factory=list)
    non_actions: list[str] = Field(default_factory=list)


class Hypothesis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    hypothesis_id: str
    statement: str
    status: HypothesisStatus = HypothesisStatus.OPEN
    supporting_finding_ids: list[str] = Field(default_factory=list)
    contradicting_finding_ids: list[str] = Field(default_factory=list)
    required_evidence: list[str] = Field(default_factory=list)


class TimelineEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str
    timestamp: datetime
    source: str
    event_type: str
    summary: str
    evidence_id: str | None = None

    @field_validator("timestamp")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timeline timestamp must include a timezone")
        return value.astimezone(UTC)


class IncidentBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")
    incident: Incident
    services: list[Service]
    dependencies: list[Dependency] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_references(self) -> IncidentBundle:
        service_ids = {service.service_id for service in self.services}
        missing_affected = set(self.incident.affected_service_ids) - service_ids
        if missing_affected:
            raise ValueError(f"unknown affected services: {sorted(missing_affected)}")
        for dependency in self.dependencies:
            refs = {dependency.source_service_id, dependency.target_service_id}
            missing = refs - service_ids
            if missing:
                raise ValueError(f"dependency references unknown services: {sorted(missing)}")
        return self


class IncidentAnalysis(BaseModel):
    incident: Incident
    services: list[Service]
    dependencies: list[Dependency]
    evidence: list[EvidenceItem]
    timeline: list[TimelineEvent]
    findings: list[Finding]
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    generated_at: datetime

    @field_validator("generated_at")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("generated_at must include a timezone")
        return value.astimezone(UTC)
