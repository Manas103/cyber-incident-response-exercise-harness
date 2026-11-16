from incident_harness.vendor.correlation import correlate_vendor_alerts
from incident_harness.vendor.fixtures import build_chained_vendor_alerts, build_standalone_vendor_alerts

N_CHAINS = 25
N_STANDALONE = 20


def test_every_chain_folds_to_exactly_one_incident():
    alerts = build_chained_vendor_alerts(N_CHAINS, seed=20261116)
    incidents = correlate_vendor_alerts(alerts)
    assert len(incidents) == N_CHAINS
    for incident in incidents:
        assert len(incident.alert_ids) == 4
        assert set(incident.feeds) == {
            "endpoint_detection", "email_gateway", "identity_provider", "managed_detection_escalation",
        }


def test_standalone_alerts_never_false_group():
    alerts = build_standalone_vendor_alerts(N_STANDALONE, seed=99)
    incidents = correlate_vendor_alerts(alerts)
    assert len(incidents) == N_STANDALONE
    for incident in incidents:
        assert len(incident.alert_ids) == 1


def test_chains_and_standalones_mixed_in_one_corpus_stay_separate():
    chained = build_chained_vendor_alerts(N_CHAINS, seed=20261116)
    standalone = build_standalone_vendor_alerts(N_STANDALONE, seed=99)
    incidents = correlate_vendor_alerts(chained + standalone)
    assert len(incidents) == N_CHAINS + N_STANDALONE
    multi_alert = [inc for inc in incidents if len(inc.alert_ids) > 1]
    single_alert = [inc for inc in incidents if len(inc.alert_ids) == 1]
    assert len(multi_alert) == N_CHAINS
    assert len(single_alert) == N_STANDALONE


def test_incident_aggregates_worst_case_severity_inputs():
    alerts = build_chained_vendor_alerts(1, seed=1)
    incidents = correlate_vendor_alerts(alerts)
    assert len(incidents) == 1
    incident = incidents[0]
    assert incident.actively_exploited is True
