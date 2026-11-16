from incident_harness.vendor.correlation import correlate_vendor_alerts
from incident_harness.vendor.fixtures import build_chained_vendor_alerts
from incident_harness.vendor.timing import compute_vendor_timing


def _one_incident():
    alerts = build_chained_vendor_alerts(1, seed=1)
    incidents = correlate_vendor_alerts(alerts)
    return incidents[0]


def test_time_to_detect_and_contain_computed_relative_to_incident_start():
    incident = _one_incident()
    timing = compute_vendor_timing(incident, ack_minutes=incident.start_minutes + 10, first_executed_contain_minutes=incident.start_minutes + 30)
    assert timing.time_to_detect_minutes == 10
    assert timing.time_to_contain_minutes == 30


def test_missing_ack_or_containment_is_none_not_zero():
    incident = _one_incident()
    timing = compute_vendor_timing(incident, ack_minutes=None, first_executed_contain_minutes=None)
    assert timing.time_to_detect_minutes is None
    assert timing.time_to_contain_minutes is None
