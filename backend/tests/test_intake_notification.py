from incident_harness.intake.fixtures import build_notification_gate_cases
from incident_harness.intake.notification import NotificationRequest, send_notification


def test_no_approver_is_held():
    result = send_notification(NotificationRequest(incident_source_reference="acct-1", message="hi", approved_by=None))
    assert result.sent is False
    assert "no named human approval" in result.reason


def test_blank_approver_is_held():
    result = send_notification(NotificationRequest(incident_source_reference="acct-1", message="hi", approved_by="   "))
    assert result.sent is False


def test_named_approver_is_sent_and_named_back():
    result = send_notification(
        NotificationRequest(incident_source_reference="acct-1", message="hi", approved_by="J. Alvarez (IR Lead)")
    )
    assert result.sent is True
    assert result.approved_by == "J. Alvarez (IR Lead)"
    assert "J. Alvarez (IR Lead)" in result.reason


def test_seeded_gate_cases_all_match_expectation():
    cases = build_notification_gate_cases(50, seed=20260801)
    assert len(cases) == 100
    for case in cases:
        result = send_notification(
            NotificationRequest(
                incident_source_reference=case.incident_source_reference,
                message=case.message,
                approved_by=case.approved_by,
            )
        )
        assert result.sent == case.expect_sent
