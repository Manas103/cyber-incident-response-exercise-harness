from incident_harness.intake.channels import (
    CHANNEL_CUSTOMER_REPORT,
    CHANNEL_INTERNAL_ALERT,
    CHANNEL_RESEARCHER_DISCLOSURE,
    CustomerReportRaw,
    InternalAlertRaw,
    ResearcherDisclosureRaw,
    normalize_customer_report,
    normalize_internal_alert,
    normalize_researcher_disclosure,
)
from incident_harness.intake.fixtures import build_channel_equivalence_cases, normalized_triple


def test_customer_report_normalizes_with_correct_channel_tag():
    raw = CustomerReportRaw(
        account_id="acct-0001",
        reported_by_email="user@example.com",
        description="login takes me to someone else's account",
        affected_product="auth-service",
        data_sensitivity="customer_pii",
        scope="single_customer",
        actively_exploited=False,
        reported_at_minutes=10,
    )
    record = normalize_customer_report(raw)
    assert record.channel == CHANNEL_CUSTOMER_REPORT
    assert record.source_reference == "acct-0001"
    assert record.data_sensitivity == "customer_pii"


def test_internal_alert_normalizes_with_correct_channel_tag():
    raw = InternalAlertRaw(
        alert_id="alert-00042",
        source_system="waf-edge",
        rule_name="sql-injection-pattern",
        data_sensitivity="payment_or_credentials",
        scope="platform_wide",
        actively_exploited=True,
        detected_at_minutes=5,
    )
    record = normalize_internal_alert(raw)
    assert record.channel == CHANNEL_INTERNAL_ALERT
    assert record.source_reference == "alert-00042"


def test_researcher_disclosure_normalizes_with_correct_channel_tag():
    raw = ResearcherDisclosureRaw(
        researcher_handle="researcher-007",
        disclosure_channel="security.txt",
        vulnerability_summary="IDOR on /api/invoices/{id}",
        data_sensitivity="customer_pii",
        scope="multiple_customers",
        actively_exploited=False,
        submitted_at_minutes=20,
    )
    record = normalize_researcher_disclosure(raw)
    assert record.channel == CHANNEL_RESEARCHER_DISCLOSURE
    assert record.source_reference == "researcher-007"


def test_all_three_channels_preserve_the_same_underlying_facts():
    cases = build_channel_equivalence_cases(20, seed=1)
    for case in cases:
        customer, internal, researcher = normalized_triple(case)
        assert customer.data_sensitivity == internal.data_sensitivity == researcher.data_sensitivity
        assert customer.scope == internal.scope == researcher.scope
        assert customer.actively_exploited == internal.actively_exploited == researcher.actively_exploited


def test_each_channel_tag_is_distinct():
    cases = build_channel_equivalence_cases(1, seed=1)
    customer, internal, researcher = normalized_triple(cases[0])
    channels = {customer.channel, internal.channel, researcher.channel}
    assert channels == {CHANNEL_CUSTOMER_REPORT, CHANNEL_INTERNAL_ALERT, CHANNEL_RESEARCHER_DISCLOSURE}
