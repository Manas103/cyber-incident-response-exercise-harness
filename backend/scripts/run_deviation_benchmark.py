"""The number-producing run behind two claims: 40 of 40 seeded playbook
deviations flagged by name, and 0 false flags over 40 clean runs.
Operates directly on the in-memory fixtures (fixtures.py), the same
way ai-governance-audit-readiness-register's run_benchmark.py calls
engine.compute_verdict directly rather than through the API."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from incident_harness.detector import detect_deviations  # noqa: E402
from incident_harness.fixtures import clean_runs, seeded_deviation_runs  # noqa: E402
from incident_harness.reference_detector import detect_deviations_reference  # noqa: E402


def main() -> None:
    seeded_cases = seeded_deviation_runs(40)
    print(f"seeded-deviation fixture: {len(seeded_cases)} runs, each with exactly one seeded deviation")

    correctly_flagged = 0
    for case in seeded_cases:
        run = case.run
        found = detect_deviations(run.run_id, run.inject_id, run.scenario_id, list(run.actions))
        matches = [
            d
            for d in found
            if d.deviation_type == case.expected_deviation_type and d.step_id == case.expected_step_id
        ]
        status = "OK" if len(found) == 1 and len(matches) == 1 else "MISS"
        if status == "OK":
            correctly_flagged += 1
        print(
            f"  {run.run_id:14s} expected={case.expected_deviation_type:14s} step={case.expected_step_id:45s} "
            f"flagged={len(found)} matched={len(matches)} -> {status}"
        )

    print(f"\nseeded_deviation_recall: {correctly_flagged}/{len(seeded_cases)}")

    clean = clean_runs(40)
    false_flags = 0
    for run in clean:
        found = detect_deviations(run.run_id, run.inject_id, run.scenario_id, list(run.actions))
        if found:
            false_flags += len(found)
            print(f"  FALSE FLAG on {run.run_id}: {[d.label() for d in found]}")
    print(f"false_flag_rate: {false_flags} false flags over {len(clean)} clean runs")

    # Reference-oracle diff over the same 80 runs, reported here too so
    # the raw output committed to docs/ shows both claims and the diff
    # in one place.
    mismatches = 0
    all_runs = [c.run for c in seeded_cases] + clean
    for run in all_runs:
        primary = detect_deviations(run.run_id, run.inject_id, run.scenario_id, list(run.actions))
        reference = detect_deviations_reference(run.run_id, run.inject_id, run.scenario_id, list(run.actions))
        primary_set = {(d.step_id, d.deviation_type) for d in primary}
        reference_set = {(d.step_id, d.deviation_type) for d in reference}
        if primary_set != reference_set:
            mismatches += 1
            print(f"  REFERENCE MISMATCH on {run.run_id}: primary={primary_set} reference={reference_set}")
    print(f"reference_oracle_mismatches: {mismatches}/{len(all_runs)}")


if __name__ == "__main__":
    main()
