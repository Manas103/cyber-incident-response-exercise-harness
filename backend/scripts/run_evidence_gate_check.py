"""Demonstrates both paths of the after-action evidence gate: the
refusal path (one of the 24 steps deliberately left without evidence)
and the success path (all 24 steps evidenced), against the same 6
official runs both times."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from incident_harness.after_action import EvidenceArtifact, generate_report  # noqa: E402
from incident_harness.fixtures import official_runs  # noqa: E402
from incident_harness.scenarios import all_steps  # noqa: E402


def _full_evidence() -> list[EvidenceArtifact]:
    evidence = []
    for run in official_runs():
        for action in run.actions:
            evidence.append(
                EvidenceArtifact(
                    run_id=run.run_id,
                    step_id=action.step_id,
                    artifact_type="log_file",
                    artifact_reference=f"logs/{run.run_id}/{action.step_id}.log",
                )
            )
    return evidence


def main() -> None:
    runs = official_runs()
    total_steps = len(all_steps())
    print(f"total named playbook steps: {total_steps}")

    print("\n--- refusal path: one step deliberately left without evidence ---")
    evidence = _full_evidence()
    withheld_step_id = evidence[0].step_id
    evidence_missing_one = [e for e in evidence if e.step_id != withheld_step_id]
    report = generate_report(runs, evidence_missing_one)
    withheld_line = next(line for line in report.lines if line.step_id == withheld_step_id)
    print(f"withheld step: {withheld_step_id}")
    print(f"withheld step status: {withheld_line.status} ({withheld_line.reason})")
    print(f"exercised: {report.exercised_count}/{report.total_steps}")
    assert withheld_line.status == "not_exercised"
    assert report.exercised_count == total_steps - 1

    print("\n--- success path: every step evidenced ---")
    report_full = generate_report(runs, evidence)
    print(f"exercised: {report_full.exercised_count}/{report_full.total_steps}")
    assert report_full.exercised_count == total_steps
    assert report_full.not_exercised_count == 0

    print("\nevidence_gate_refusal: true (refuses without evidence, confirms with evidence)")


if __name__ == "__main__":
    main()
