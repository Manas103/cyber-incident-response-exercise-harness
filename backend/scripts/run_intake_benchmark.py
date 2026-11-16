"""The 3 benchmarks behind the intake extension's claims: channel-normalization
equivalence, the severity-oracle diff, and the notification approval gate. Run from
backend/."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from incident_harness.intake.fixtures import (  # noqa: E402
    build_channel_equivalence_cases,
    build_notification_gate_cases,
    build_severity_inputs_sample,
    normalized_triple,
)
from incident_harness.intake.notification import NotificationRequest, send_notification  # noqa: E402
from incident_harness.intake.reference_severity_oracle import classify_severity_reference  # noqa: E402
from incident_harness.intake.severity import classify_severity  # noqa: E402

SEED = 20260801


def run_channel_normalization(n: int = 100) -> None:
    cases = build_channel_equivalence_cases(n, seed=SEED)
    mismatches = 0
    for case in cases:
        customer, internal, researcher = normalized_triple(case)
        facts = {
            (r.data_sensitivity, r.scope, r.actively_exploited) for r in (customer, internal, researcher)
        }
        if len(facts) != 1:
            mismatches += 1
    print(f"--- claim: 3 incoming report channels normalized onto one incident record ---")
    print(f"seeded cases: {n}")
    print(f"cases where all 3 channels normalized to identical (data_sensitivity, scope, actively_exploited): {n - mismatches} / {n}")
    print(f"mismatches: {mismatches}")


def run_severity_oracle_diff(n: int = 500) -> None:
    inputs_sample = build_severity_inputs_sample(n, seed=SEED)
    matches = 0
    mismatches = []
    for inputs in inputs_sample:
        primary = classify_severity(inputs)
        reference = classify_severity_reference(inputs)
        if primary == reference:
            matches += 1
        else:
            mismatches.append((inputs, primary, reference))
    print(f"--- claim: severity classified against a written matrix checked by an independent oracle ---")
    print(f"seeded cases: {n}")
    print(f"primary matched independent reference oracle: {matches} / {n}")
    for inputs, primary, reference in mismatches[:5]:
        print(f"  mismatch: {inputs} primary={primary} reference={reference}")


def run_notification_gate(n_each: int = 50) -> None:
    cases = build_notification_gate_cases(n_each, seed=SEED)
    correct = 0
    false_sends = 0
    false_holds = 0
    for case in cases:
        result = send_notification(
            NotificationRequest(
                incident_source_reference=case.incident_source_reference,
                message=case.message,
                approved_by=case.approved_by,
            )
        )
        if result.sent == case.expect_sent:
            correct += 1
        elif result.sent and not case.expect_sent:
            false_sends += 1
        elif not result.sent and case.expect_sent:
            false_holds += 1
    print(f"--- claim: every customer notification held behind a named human approval ---")
    print(f"seeded cases: {len(cases)} ({n_each} without approval, {n_each} with named approval)")
    print(f"correct gate decision: {correct} / {len(cases)}")
    print(f"false sends (sent without approval): {false_sends}")
    print(f"false holds (approved but not sent): {false_holds}")


if __name__ == "__main__":
    run_channel_normalization()
    print()
    run_severity_oracle_diff()
    print()
    run_notification_gate()
