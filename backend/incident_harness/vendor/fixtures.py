"""Seeded, deterministic fixtures for the vendor-feed extension's benchmarks:
correlation (25 believable intrusion chains + 20 standalone alerts), the
severity-oracle diff over vendor-derived inputs (500 cases), and the
containment approval gate (100 decisions). Every host, user, IP and message
here is synthetic, describing a fictional company's telemetry."""

import random
from dataclasses import dataclass

from ..intake.severity import SeverityInputs
from .containment import ACTION_HOST_ISOLATION, ACTION_SESSION_REVOKE, ACTION_TOKEN_RESET, ContainmentRequest
from .feeds import (
    EmailGatewayRaw,
    EndpointDetectionRaw,
    IdentityProviderRaw,
    ManagedDetectionEscalationRaw,
    VendorAlert,
    normalize_email_gateway,
    normalize_endpoint_detection,
    normalize_identity_provider,
    normalize_mdr_escalation,
)

DATA_SENSITIVITIES = ("none", "internal_only", "customer_pii", "payment_or_credentials")
SCOPES = ("single_customer", "multiple_customers", "platform_wide")

USERS = [f"user{i:04d}@example.com" for i in range(1, 60)]
HOSTS = [f"WKS-{i:04d}" for i in range(1, 60)]


def build_chained_vendor_alerts(n_chains: int, seed: int) -> list[VendorAlert]:
    """n_chains intrusion narratives, each exactly 4 alerts, one per feed, sharing
    a user entity (identity provider -> email gateway) and a host entity
    (endpoint detection -> MDR escalation), with the MDR escalation naming both
    and so bridging the two halves into one connected component."""
    rng = random.Random(seed)
    alerts: list[VendorAlert] = []
    for i in range(n_chains):
        user = USERS[i % len(USERS)]
        host = HOSTS[i % len(HOSTS)]
        base_t = i * 500
        sensitivity = rng.choice(DATA_SENSITIVITIES)
        scope = rng.choice(SCOPES)

        alerts.append(
            normalize_identity_provider(
                IdentityProviderRaw(
                    event_id=f"idp-{i:04d}",
                    user=user,
                    source_ip=f"203.0.113.{i % 250}",
                    risk_event_type="impossible_travel",
                    data_sensitivity="none",
                    scope="single_customer",
                    actively_exploited=False,
                    observed_at_minutes=base_t,
                )
            )
        )
        alerts.append(
            normalize_email_gateway(
                EmailGatewayRaw(
                    message_id=f"msg-{i:04d}",
                    recipient_user=user,
                    sender_domain="external-lookalike.example",
                    verdict="phishing_delivered",
                    data_sensitivity="none",
                    scope="single_customer",
                    actively_exploited=False,
                    delivered_at_minutes=base_t + 15,
                )
            )
        )
        alerts.append(
            normalize_endpoint_detection(
                EndpointDetectionRaw(
                    detection_id=f"edr-{i:04d}",
                    host=host,
                    process_name="powershell.exe",
                    rule_name="suspicious_macro_spawned_shell",
                    data_sensitivity="none",
                    scope="single_customer",
                    actively_exploited=False,
                    detected_at_minutes=base_t + 40,
                )
            )
        )
        alerts.append(
            normalize_mdr_escalation(
                ManagedDetectionEscalationRaw(
                    escalation_id=f"mdr-{i:04d}",
                    host=host,
                    user=user,
                    escalation_reason="phishing-to-shell chain confirmed by vendor SOC",
                    data_sensitivity=sensitivity,
                    scope=scope,
                    actively_exploited=True,
                    escalated_at_minutes=base_t + 55,
                )
            )
        )
    return alerts


def build_standalone_vendor_alerts(n: int, seed: int) -> list[VendorAlert]:
    """n one-off alerts, each with a unique, non-overlapping entity and a
    timestamp far from any other alert, so none can ever correlate with
    another by construction; the false-grouping check."""
    rng = random.Random(seed)
    alerts: list[VendorAlert] = []
    for i in range(n):
        base_t = 1_000_000 + i * 10_000
        kind = i % 4
        if kind == 0:
            alerts.append(
                normalize_endpoint_detection(
                    EndpointDetectionRaw(
                        detection_id=f"standalone-edr-{i:04d}",
                        host=f"STANDALONE-HOST-{i:04d}",
                        process_name="notepad.exe",
                        rule_name="benign_baseline_change",
                        data_sensitivity=rng.choice(DATA_SENSITIVITIES),
                        scope="single_customer",
                        actively_exploited=False,
                        detected_at_minutes=base_t,
                    )
                )
            )
        elif kind == 1:
            alerts.append(
                normalize_email_gateway(
                    EmailGatewayRaw(
                        message_id=f"standalone-msg-{i:04d}",
                        recipient_user=f"standalone-user-{i:04d}@example.com",
                        sender_domain="known-partner.example",
                        verdict="quarantined_spam",
                        data_sensitivity=rng.choice(DATA_SENSITIVITIES),
                        scope="single_customer",
                        actively_exploited=False,
                        delivered_at_minutes=base_t,
                    )
                )
            )
        elif kind == 2:
            alerts.append(
                normalize_identity_provider(
                    IdentityProviderRaw(
                        event_id=f"standalone-idp-{i:04d}",
                        user=f"standalone-user-{i:04d}@example.com",
                        source_ip=f"198.51.100.{i % 250}",
                        risk_event_type="new_device_login",
                        data_sensitivity=rng.choice(DATA_SENSITIVITIES),
                        scope="single_customer",
                        actively_exploited=False,
                        observed_at_minutes=base_t,
                    )
                )
            )
        else:
            alerts.append(
                normalize_mdr_escalation(
                    ManagedDetectionEscalationRaw(
                        escalation_id=f"standalone-mdr-{i:04d}",
                        host=f"STANDALONE-HOST-{i:04d}",
                        user=f"standalone-user-{i:04d}@example.com",
                        escalation_reason="vendor SOC closed as isolated false positive",
                        data_sensitivity=rng.choice(DATA_SENSITIVITIES),
                        scope="single_customer",
                        actively_exploited=False,
                        escalated_at_minutes=base_t,
                    )
                )
            )
    return alerts


def build_vendor_severity_sample(n: int, seed: int) -> list[SeverityInputs]:
    """n seeded samples over the same 4 x 3 x 2 = 24 combinations the written
    severity matrix is defined over, derived from vendor-incident-shaped
    inputs rather than intake/fixtures.py's report-shaped ones; every
    combination appears at least once first, the same exhaustive-then-pad
    approach as the intake extension."""
    all_combinations = [
        SeverityInputs(data_sensitivity=s, scope=sc, actively_exploited=e)
        for s in DATA_SENSITIVITIES
        for sc in SCOPES
        for e in (True, False)
    ]
    rng = random.Random(seed)
    if n <= len(all_combinations):
        return rng.sample(all_combinations, n)
    extra = [rng.choice(all_combinations) for _ in range(n - len(all_combinations))]
    return all_combinations + extra


@dataclass(frozen=True)
class ContainmentGateCase:
    request: ContainmentRequest
    expect_executed: bool


def build_containment_gate_cases(n_each: int, seed: int) -> list[ContainmentGateCase]:
    """n_each unapproved requests (must refuse, 0 executed) and n_each approved
    requests (must execute), spread evenly across the 3 action types so every
    action type is exercised both ways."""
    rng = random.Random(seed)
    approvers = ["J. Alvarez (IR Lead)", "M. Chen (Trust & Safety Manager)", "R. Okafor (CISO delegate)"]
    action_types = [ACTION_HOST_ISOLATION, ACTION_SESSION_REVOKE, ACTION_TOKEN_RESET]
    cases = []
    for i in range(n_each):
        action_type = action_types[i % len(action_types)]
        cases.append(
            ContainmentGateCase(
                request=ContainmentRequest(
                    action_id=f"unapproved-{i:04d}",
                    incident_id=f"VINC-seeded-{i:04d}",
                    action_type=action_type,
                    target_entity=f"target-{i:04d}",
                    action_minutes=i,
                    approved_by=None,
                ),
                expect_executed=False,
            )
        )
    for i in range(n_each):
        action_type = action_types[i % len(action_types)]
        cases.append(
            ContainmentGateCase(
                request=ContainmentRequest(
                    action_id=f"approved-{i:04d}",
                    incident_id=f"VINC-seeded-{i:04d}",
                    action_type=action_type,
                    target_entity=f"target-approved-{i:04d}",
                    action_minutes=i,
                    approved_by=rng.choice(approvers),
                ),
                expect_executed=True,
            )
        )
    return cases
