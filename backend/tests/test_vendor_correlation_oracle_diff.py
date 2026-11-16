from incident_harness.vendor.correlation import correlate_vendor_alerts
from incident_harness.vendor.fixtures import build_chained_vendor_alerts, build_standalone_vendor_alerts
from incident_harness.vendor.reference_correlation import correlate_vendor_alerts_reference


def test_primary_and_reference_correlation_agree_exactly():
    chained = build_chained_vendor_alerts(25, seed=20261116)
    standalone = build_standalone_vendor_alerts(20, seed=99)
    alerts = chained + standalone

    primary = correlate_vendor_alerts(alerts)
    reference = correlate_vendor_alerts_reference(alerts)

    primary_keys = sorted(inc.content_key() for inc in primary)
    reference_keys = sorted(inc.content_key() for inc in reference)

    assert len(primary) == len(reference)
    assert primary_keys == reference_keys
