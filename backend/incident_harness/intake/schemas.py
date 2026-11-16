"""Pydantic request/response shapes for the intake extension's API surface."""

from pydantic import BaseModel


class CustomerReportIn(BaseModel):
    account_id: str
    reported_by_email: str
    description: str
    affected_product: str
    data_sensitivity: str
    scope: str
    actively_exploited: bool
    reported_at_minutes: int


class InternalAlertIn(BaseModel):
    alert_id: str
    source_system: str
    rule_name: str
    data_sensitivity: str
    scope: str
    actively_exploited: bool
    detected_at_minutes: int


class ResearcherDisclosureIn(BaseModel):
    researcher_handle: str
    disclosure_channel: str
    vulnerability_summary: str
    data_sensitivity: str
    scope: str
    actively_exploited: bool
    submitted_at_minutes: int


class IncidentRecordOut(BaseModel):
    incident_id: int
    channel: str
    source_reference: str
    summary: str
    data_sensitivity: str
    scope: str
    actively_exploited: bool
    reported_at_minutes: int
    severity: str


class NotificationIn(BaseModel):
    incident_id: int
    message: str
    approved_by: str | None = None


class NotificationOut(BaseModel):
    incident_id: int
    sent: bool
    reason: str
    approved_by: str | None
