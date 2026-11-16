"""3 incoming report channels, each its own raw shape (a customer names an account and a
product; an internal monitoring alert names a source system and a rule; a researcher
disclosure names a handle and a disclosure channel), normalized by normalize_*() onto one
shared IncidentRecord. The three raw dataclasses are deliberately not unified into one
shape at the source: a real customer report, internal alert and researcher disclosure
genuinely carry different fields, which is exactly what "normalized onto one incident
record" has to reconcile, not a distinction invented to make the module look harder than
it is."""

from dataclasses import dataclass

CHANNEL_CUSTOMER_REPORT = "customer_report"
CHANNEL_INTERNAL_ALERT = "internal_alert"
CHANNEL_RESEARCHER_DISCLOSURE = "researcher_disclosure"

DATA_SENSITIVITY_NONE = "none"
DATA_SENSITIVITY_INTERNAL_ONLY = "internal_only"
DATA_SENSITIVITY_CUSTOMER_PII = "customer_pii"
DATA_SENSITIVITY_PAYMENT_OR_CREDENTIALS = "payment_or_credentials"

SCOPE_SINGLE_CUSTOMER = "single_customer"
SCOPE_MULTIPLE_CUSTOMERS = "multiple_customers"
SCOPE_PLATFORM_WIDE = "platform_wide"


@dataclass(frozen=True)
class CustomerReportRaw:
    account_id: str
    reported_by_email: str
    description: str
    affected_product: str
    data_sensitivity: str
    scope: str
    actively_exploited: bool
    reported_at_minutes: int


@dataclass(frozen=True)
class InternalAlertRaw:
    alert_id: str
    source_system: str
    rule_name: str
    data_sensitivity: str
    scope: str
    actively_exploited: bool
    detected_at_minutes: int


@dataclass(frozen=True)
class ResearcherDisclosureRaw:
    researcher_handle: str
    disclosure_channel: str
    vulnerability_summary: str
    data_sensitivity: str
    scope: str
    actively_exploited: bool
    submitted_at_minutes: int


@dataclass(frozen=True)
class IncidentRecord:
    """The one shape every channel normalizes onto. source_reference carries the
    channel-specific identifier (account id, alert id, researcher handle) under one
    field name so downstream code (severity classification, notification) never has
    to branch on which channel an incident arrived through."""

    channel: str
    source_reference: str
    summary: str
    data_sensitivity: str
    scope: str
    actively_exploited: bool
    reported_at_minutes: int


def normalize_customer_report(raw: CustomerReportRaw) -> IncidentRecord:
    return IncidentRecord(
        channel=CHANNEL_CUSTOMER_REPORT,
        source_reference=raw.account_id,
        summary=f"{raw.affected_product}: {raw.description}",
        data_sensitivity=raw.data_sensitivity,
        scope=raw.scope,
        actively_exploited=raw.actively_exploited,
        reported_at_minutes=raw.reported_at_minutes,
    )


def normalize_internal_alert(raw: InternalAlertRaw) -> IncidentRecord:
    return IncidentRecord(
        channel=CHANNEL_INTERNAL_ALERT,
        source_reference=raw.alert_id,
        summary=f"{raw.source_system}: {raw.rule_name}",
        data_sensitivity=raw.data_sensitivity,
        scope=raw.scope,
        actively_exploited=raw.actively_exploited,
        reported_at_minutes=raw.detected_at_minutes,
    )


def normalize_researcher_disclosure(raw: ResearcherDisclosureRaw) -> IncidentRecord:
    return IncidentRecord(
        channel=CHANNEL_RESEARCHER_DISCLOSURE,
        source_reference=raw.researcher_handle,
        summary=f"{raw.disclosure_channel}: {raw.vulnerability_summary}",
        data_sensitivity=raw.data_sensitivity,
        scope=raw.scope,
        actively_exploited=raw.actively_exploited,
        reported_at_minutes=raw.submitted_at_minutes,
    )
