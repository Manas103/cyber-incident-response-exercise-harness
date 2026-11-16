"""Seeded, deterministic fixtures for the intake extension's 3 benchmarks: channel
normalization, the severity-oracle diff, and the notification approval gate. Every
incident, approver name and report body here is synthetic, describing a fictional
company's reports, exactly like fixtures.py above for the exercise scenarios."""

import random
from dataclasses import dataclass

from .channels import (
    CustomerReportRaw,
    InternalAlertRaw,
    IncidentRecord,
    ResearcherDisclosureRaw,
    normalize_customer_report,
    normalize_internal_alert,
    normalize_researcher_disclosure,
)
from .severity import SeverityInputs

DATA_SENSITIVITIES = ("none", "internal_only", "customer_pii", "payment_or_credentials")
SCOPES = ("single_customer", "multiple_customers", "platform_wide")

CUSTOMER_ACCOUNTS = [f"acct-{i:04d}" for i in range(1, 51)]
INTERNAL_SOURCE_SYSTEMS = ["edr-fleet", "waf-edge", "iam-anomaly", "siem-correlation"]
RESEARCHER_HANDLES = [f"researcher-{i:03d}" for i in range(1, 21)]


@dataclass(frozen=True)
class ChannelEquivalenceCase:
    """3 raw reports, one per channel, describing the same underlying facts
    (data_sensitivity, scope, actively_exploited); normalization must preserve those 3
    facts identically across all three channels even though the raw shapes differ."""

    customer_report: CustomerReportRaw
    internal_alert: InternalAlertRaw
    researcher_disclosure: ResearcherDisclosureRaw


def build_channel_equivalence_cases(n: int, seed: int) -> list[ChannelEquivalenceCase]:
    rng = random.Random(seed)
    cases = []
    for i in range(n):
        sensitivity = rng.choice(DATA_SENSITIVITIES)
        scope = rng.choice(SCOPES)
        exploited = rng.choice([True, False])
        cases.append(
            ChannelEquivalenceCase(
                customer_report=CustomerReportRaw(
                    account_id=rng.choice(CUSTOMER_ACCOUNTS),
                    reported_by_email=f"user{i}@example.com",
                    description=f"seeded customer report {i}",
                    affected_product="billing-api",
                    data_sensitivity=sensitivity,
                    scope=scope,
                    actively_exploited=exploited,
                    reported_at_minutes=i,
                ),
                internal_alert=InternalAlertRaw(
                    alert_id=f"alert-{i:05d}",
                    source_system=rng.choice(INTERNAL_SOURCE_SYSTEMS),
                    rule_name=f"seeded-rule-{i}",
                    data_sensitivity=sensitivity,
                    scope=scope,
                    actively_exploited=exploited,
                    detected_at_minutes=i,
                ),
                researcher_disclosure=ResearcherDisclosureRaw(
                    researcher_handle=rng.choice(RESEARCHER_HANDLES),
                    disclosure_channel="security.txt",
                    vulnerability_summary=f"seeded disclosure {i}",
                    data_sensitivity=sensitivity,
                    scope=scope,
                    actively_exploited=exploited,
                    submitted_at_minutes=i,
                ),
            )
        )
    return cases


def normalized_triple(case: ChannelEquivalenceCase) -> tuple[IncidentRecord, IncidentRecord, IncidentRecord]:
    return (
        normalize_customer_report(case.customer_report),
        normalize_internal_alert(case.internal_alert),
        normalize_researcher_disclosure(case.researcher_disclosure),
    )


def build_severity_inputs_sample(n: int, seed: int) -> list[SeverityInputs]:
    """n seeded samples over the 4 x 3 x 2 = 24 possible combinations, with repeats;
    every one of the 24 combinations is guaranteed to appear at least once first, the
    same exhaustive-then-pad approach as fixtures.py above."""
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
class NotificationGateCase:
    incident_source_reference: str
    message: str
    approved_by: str | None
    expect_sent: bool


def build_notification_gate_cases(n_each: int, seed: int) -> list[NotificationGateCase]:
    rng = random.Random(seed)
    approvers = ["J. Alvarez (IR Lead)", "M. Chen (Trust & Safety Manager)", "R. Okafor (CISO delegate)"]
    cases = []
    for i in range(n_each):
        cases.append(
            NotificationGateCase(
                incident_source_reference=f"acct-{i:04d}",
                message=f"seeded notification without approval {i}",
                approved_by=None,
                expect_sent=False,
            )
        )
    for i in range(n_each):
        cases.append(
            NotificationGateCase(
                incident_source_reference=f"acct-{i:04d}",
                message=f"seeded notification with approval {i}",
                approved_by=rng.choice(approvers),
                expect_sent=True,
            )
        )
    return cases
