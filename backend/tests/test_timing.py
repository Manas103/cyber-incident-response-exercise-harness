from incident_harness.detector import ActionRecord
from incident_harness.injects import INJECT_BY_ID
from incident_harness.timing import compute_timing


def test_time_to_detect_and_contain_are_measured_relative_to_the_inject():
    inject = INJECT_BY_ID["ransomware_corporate_it.inject1"]
    actions = [
        ActionRecord("detected", inject.timestamp_minutes + 5, "ransomware_corporate_it.detect"),
        ActionRecord("contained", inject.timestamp_minutes + 15, "ransomware_corporate_it.contain"),
    ]
    timing = compute_timing(inject, actions)
    assert timing.time_to_detect_minutes == 5
    assert timing.time_to_contain_minutes == 15


def test_timing_is_none_when_the_matching_action_never_happened():
    inject = INJECT_BY_ID["ransomware_corporate_it.inject1"]
    timing = compute_timing(inject, [])
    assert timing.time_to_detect_minutes is None
    assert timing.time_to_contain_minutes is None


def test_timing_uses_the_earliest_matching_action_not_the_last():
    inject = INJECT_BY_ID["ransomware_corporate_it.inject1"]
    actions = [
        ActionRecord("detected late", inject.timestamp_minutes + 20, "ransomware_corporate_it.detect"),
        ActionRecord("detected early", inject.timestamp_minutes + 5, "ransomware_corporate_it.detect"),
    ]
    timing = compute_timing(inject, actions)
    assert timing.time_to_detect_minutes == 5


def test_timing_never_references_an_action_from_a_different_scenario():
    inject = INJECT_BY_ID["ransomware_corporate_it.inject1"]
    actions = [ActionRecord("foreign detect", inject.timestamp_minutes + 1, "phishing_credential_compromise.detect")]
    timing = compute_timing(inject, actions)
    assert timing.time_to_detect_minutes is None
