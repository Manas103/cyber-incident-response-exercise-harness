"""The 3 benchmarks behind the vendor-feed extension's claims: entity-and-time
correlation folding 4 vendor feeds onto one incident record, the severity-oracle
diff over vendor-derived inputs, and the containment approval gate with its
reversibility check. Run from backend/."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from incident_harness.intake.reference_severity_oracle import classify_severity_reference  # noqa: E402
from incident_harness.intake.severity import classify_severity  # noqa: E402
from incident_harness.vendor.containment import EntityStateStore, STATE_NORMAL, apply_containment, undo_containment  # noqa: E402
from incident_harness.vendor.correlation import correlate_vendor_alerts  # noqa: E402
from incident_harness.vendor.fixtures import (  # noqa: E402
    build_chained_vendor_alerts,
    build_containment_gate_cases,
    build_standalone_vendor_alerts,
    build_vendor_severity_sample,
)
from incident_harness.vendor.reference_correlation import correlate_vendor_alerts_reference  # noqa: E402

SEED = 20261116
N_CHAINS = 25
N_STANDALONE = 20
N_GATE_EACH = 50
N_SEVERITY = 500


def run_correlation() -> None:
    chained = build_chained_vendor_alerts(N_CHAINS, seed=SEED)
    standalone = build_standalone_vendor_alerts(N_STANDALONE, seed=99)
    alerts = chained + standalone

    incidents = correlate_vendor_alerts(alerts)
    reference = correlate_vendor_alerts_reference(alerts)
    primary_keys = sorted(inc.content_key() for inc in incidents)
    reference_keys = sorted(inc.content_key() for inc in reference)

    multi_alert = [inc for inc in incidents if len(inc.alert_ids) > 1]
    single_alert = [inc for inc in incidents if len(inc.alert_ids) == 1]

    print("--- claim: 4 vendor alert feeds normalized onto one incident record ---")
    print(f"alerts ingested: {len(alerts)} ({N_CHAINS} chains x 4 feeds + {N_STANDALONE} standalone)")
    print(f"chains correctly folded to 1 incident each: {len(multi_alert)} / {N_CHAINS}")
    print(f"false groupings among standalone alerts: {N_STANDALONE - len(single_alert)} / {N_STANDALONE}")
    print(f"primary vs. reference correlation engine: {len(incidents)} vs {len(reference)} incidents, exact agreement = {primary_keys == reference_keys}")


def run_severity_oracle_diff() -> None:
    sample = build_vendor_severity_sample(N_SEVERITY, seed=SEED)
    matches = sum(1 for inputs in sample if classify_severity(inputs) == classify_severity_reference(inputs))
    print("--- claim: severity classified against a written matrix matching an independent oracle on 500 of 500 cases ---")
    print(f"seeded cases: {N_SEVERITY}")
    print(f"primary matched independent reference oracle: {matches} / {N_SEVERITY}")


def run_containment_gate() -> None:
    cases = build_containment_gate_cases(N_GATE_EACH, seed=SEED)
    store = EntityStateStore()
    correct = 0
    unapproved_executed = 0
    executed = []
    for case in cases:
        result = apply_containment(case.request, store)
        if result.executed == case.expect_executed:
            correct += 1
        if case.request.approved_by is None and result.executed:
            unapproved_executed += 1
        if result.executed:
            executed.append((case.request, result))

    reverted = 0
    for request, result in executed:
        undo = undo_containment(request, result, store)
        if undo.undone and store.state_of(request.target_entity) == STATE_NORMAL:
            reverted += 1

    print("--- claim: containment runs only behind a named approver; 100 of 100 gate decisions correct; 0 unapproved actions; every action reversible ---")
    print(f"gate decisions: {len(cases)} ({N_GATE_EACH} unapproved + {N_GATE_EACH} approved)")
    print(f"correct gate decision: {correct} / {len(cases)}")
    print(f"unapproved actions executed: {unapproved_executed} / {N_GATE_EACH}")
    print(f"executed (approved) actions: {len(executed)} / {N_GATE_EACH}")
    print(f"executed actions successfully reverted to normal: {reverted} / {len(executed)}")


if __name__ == "__main__":
    run_correlation()
    print()
    run_severity_oracle_diff()
    print()
    run_containment_gate()
