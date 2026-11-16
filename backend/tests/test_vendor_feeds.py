from incident_harness.vendor.feeds import (
    EmailGatewayRaw,
    EndpointDetectionRaw,
    ENTITY_HOST,
    ENTITY_USER,
    FEED_EMAIL_GATEWAY,
    FEED_ENDPOINT_DETECTION,
    FEED_IDENTITY_PROVIDER,
    FEED_MDR_ESCALATION,
    IdentityProviderRaw,
    ManagedDetectionEscalationRaw,
    normalize_email_gateway,
    normalize_endpoint_detection,
    normalize_identity_provider,
    normalize_mdr_escalation,
)


def test_endpoint_detection_normalizes_to_a_host_only_entity():
    raw = EndpointDetectionRaw(
        detection_id="edr-1", host="WKS-0001", process_name="powershell.exe",
        rule_name="r", data_sensitivity="none", scope="single_customer",
        actively_exploited=False, detected_at_minutes=10,
    )
    alert = normalize_endpoint_detection(raw)
    assert alert.feed == FEED_ENDPOINT_DETECTION
    assert alert.entities == ((ENTITY_HOST, "WKS-0001"),)
    assert alert.timestamp_minutes == 10


def test_email_gateway_normalizes_to_a_user_only_entity():
    raw = EmailGatewayRaw(
        message_id="msg-1", recipient_user="a@example.com", sender_domain="x.example",
        verdict="phishing_delivered", data_sensitivity="none", scope="single_customer",
        actively_exploited=False, delivered_at_minutes=5,
    )
    alert = normalize_email_gateway(raw)
    assert alert.feed == FEED_EMAIL_GATEWAY
    assert alert.entities == ((ENTITY_USER, "a@example.com"),)


def test_identity_provider_normalizes_to_a_user_only_entity():
    raw = IdentityProviderRaw(
        event_id="idp-1", user="a@example.com", source_ip="203.0.113.1",
        risk_event_type="impossible_travel", data_sensitivity="none", scope="single_customer",
        actively_exploited=False, observed_at_minutes=1,
    )
    alert = normalize_identity_provider(raw)
    assert alert.feed == FEED_IDENTITY_PROVIDER
    assert alert.entities == ((ENTITY_USER, "a@example.com"),)


def test_mdr_escalation_normalizes_to_both_a_host_and_a_user_entity():
    raw = ManagedDetectionEscalationRaw(
        escalation_id="mdr-1", host="WKS-0001", user="a@example.com",
        escalation_reason="confirmed", data_sensitivity="customer_pii",
        scope="single_customer", actively_exploited=True, escalated_at_minutes=55,
    )
    alert = normalize_mdr_escalation(raw)
    assert alert.feed == FEED_MDR_ESCALATION
    assert set(alert.entities) == {(ENTITY_HOST, "WKS-0001"), (ENTITY_USER, "a@example.com")}
