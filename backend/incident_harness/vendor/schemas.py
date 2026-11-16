"""Pydantic request/response shapes for the vendor-feed extension's API surface."""

from pydantic import BaseModel


class EndpointDetectionIn(BaseModel):
    detection_id: str
    host: str
    process_name: str
    rule_name: str
    data_sensitivity: str
    scope: str
    actively_exploited: bool
    detected_at_minutes: int


class EmailGatewayIn(BaseModel):
    message_id: str
    recipient_user: str
    sender_domain: str
    verdict: str
    data_sensitivity: str
    scope: str
    actively_exploited: bool
    delivered_at_minutes: int


class IdentityProviderIn(BaseModel):
    event_id: str
    user: str
    source_ip: str
    risk_event_type: str
    data_sensitivity: str
    scope: str
    actively_exploited: bool
    observed_at_minutes: int


class ManagedDetectionEscalationIn(BaseModel):
    escalation_id: str
    host: str
    user: str
    escalation_reason: str
    data_sensitivity: str
    scope: str
    actively_exploited: bool
    escalated_at_minutes: int


class VendorAlertOut(BaseModel):
    alert_id: str
    feed: str
    entities: list[list[str]]
    summary: str
    data_sensitivity: str
    scope: str
    actively_exploited: bool
    timestamp_minutes: int


class VendorIncidentOut(BaseModel):
    incident_id: str
    alert_ids: list[str]
    feeds: list[str]
    entities: list[list[str]]
    start_minutes: int
    end_minutes: int
    data_sensitivity: str
    scope: str
    actively_exploited: bool
    severity: str
    time_to_detect_minutes: int | None
    time_to_contain_minutes: int | None


class AnalystAckIn(BaseModel):
    incident_id: str
    analyst_name: str
    ack_minutes: int


class ContainmentActionIn(BaseModel):
    action_id: str
    incident_id: str
    action_type: str
    target_entity: str
    action_minutes: int
    approved_by: str | None = None


class ContainmentActionOut(BaseModel):
    action_id: str
    incident_id: str
    action_type: str
    target_entity: str
    action_minutes: int
    approved_by: str | None
    executed: bool
    reason: str
    state_before: str | None
    state_after: str | None
    undone: bool


class AcceptedOut(BaseModel):
    accepted: bool


class UndoOut(BaseModel):
    action_id: str
    undone: bool
    reason: str
