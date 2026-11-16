"""4 vendor-shaped alert feeds, each its own raw shape, normalized by normalize_*() onto
one shared VendorAlert. Unlike intake/channels.py's 3 report channels (a human reporting
an incident through a different door), these 4 are the always-on vendor telemetry a
lean, vendor-leveraged SOC actually watches: an EDR console, an email security gateway,
an identity provider's risk feed, and a managed-detection-and-response vendor's own
escalation queue. Each carries a different entity shape (host-only, user-only, or both),
which is exactly what correlation.py has to reconcile to fold 4 differently-shaped feeds
into one incident record."""

from dataclasses import dataclass

FEED_ENDPOINT_DETECTION = "endpoint_detection"
FEED_EMAIL_GATEWAY = "email_gateway"
FEED_IDENTITY_PROVIDER = "identity_provider"
FEED_MDR_ESCALATION = "managed_detection_escalation"

ENTITY_HOST = "host"
ENTITY_USER = "user"


@dataclass(frozen=True)
class EndpointDetectionRaw:
    detection_id: str
    host: str
    process_name: str
    rule_name: str
    data_sensitivity: str
    scope: str
    actively_exploited: bool
    detected_at_minutes: int


@dataclass(frozen=True)
class EmailGatewayRaw:
    message_id: str
    recipient_user: str
    sender_domain: str
    verdict: str
    data_sensitivity: str
    scope: str
    actively_exploited: bool
    delivered_at_minutes: int


@dataclass(frozen=True)
class IdentityProviderRaw:
    event_id: str
    user: str
    source_ip: str
    risk_event_type: str
    data_sensitivity: str
    scope: str
    actively_exploited: bool
    observed_at_minutes: int


@dataclass(frozen=True)
class ManagedDetectionEscalationRaw:
    escalation_id: str
    host: str
    user: str
    escalation_reason: str
    data_sensitivity: str
    scope: str
    actively_exploited: bool
    escalated_at_minutes: int


@dataclass(frozen=True)
class VendorAlert:
    """The one shape every feed normalizes onto. entities is a tuple of (entity_type,
    value) pairs rather than a dict so it stays hashable and sortable for the
    correlation engines below; a feed contributes 1 or 2 entity pairs depending on
    what it natively observes (an email gateway never sees a hostname; an endpoint
    agent never sees a user principal; MDR escalations, which already triaged across
    tools, carry both)."""

    alert_id: str
    feed: str
    entities: tuple[tuple[str, str], ...]
    summary: str
    data_sensitivity: str
    scope: str
    actively_exploited: bool
    timestamp_minutes: int


def normalize_endpoint_detection(raw: EndpointDetectionRaw) -> VendorAlert:
    return VendorAlert(
        alert_id=raw.detection_id,
        feed=FEED_ENDPOINT_DETECTION,
        entities=((ENTITY_HOST, raw.host),),
        summary=f"{raw.rule_name} on {raw.process_name}",
        data_sensitivity=raw.data_sensitivity,
        scope=raw.scope,
        actively_exploited=raw.actively_exploited,
        timestamp_minutes=raw.detected_at_minutes,
    )


def normalize_email_gateway(raw: EmailGatewayRaw) -> VendorAlert:
    return VendorAlert(
        alert_id=raw.message_id,
        feed=FEED_EMAIL_GATEWAY,
        entities=((ENTITY_USER, raw.recipient_user),),
        summary=f"{raw.verdict} from {raw.sender_domain}",
        data_sensitivity=raw.data_sensitivity,
        scope=raw.scope,
        actively_exploited=raw.actively_exploited,
        timestamp_minutes=raw.delivered_at_minutes,
    )


def normalize_identity_provider(raw: IdentityProviderRaw) -> VendorAlert:
    return VendorAlert(
        alert_id=raw.event_id,
        feed=FEED_IDENTITY_PROVIDER,
        entities=((ENTITY_USER, raw.user),),
        summary=f"{raw.risk_event_type} from {raw.source_ip}",
        data_sensitivity=raw.data_sensitivity,
        scope=raw.scope,
        actively_exploited=raw.actively_exploited,
        timestamp_minutes=raw.observed_at_minutes,
    )


def normalize_mdr_escalation(raw: ManagedDetectionEscalationRaw) -> VendorAlert:
    return VendorAlert(
        alert_id=raw.escalation_id,
        feed=FEED_MDR_ESCALATION,
        entities=((ENTITY_HOST, raw.host), (ENTITY_USER, raw.user)),
        summary=raw.escalation_reason,
        data_sensitivity=raw.data_sensitivity,
        scope=raw.scope,
        actively_exploited=raw.actively_exploited,
        timestamp_minutes=raw.escalated_at_minutes,
    )
