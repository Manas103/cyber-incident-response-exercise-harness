"""The after-action evidence gate, both paths: refusal (a step
deliberately left without evidence) and success (every step
evidenced), against the same 24-step, 6-run official exercise."""

from incident_harness.after_action import EvidenceArtifact, generate_report
from incident_harness.fixtures import official_runs
from incident_harness.scenarios import all_steps


def _full_evidence():
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


def test_success_path_marks_all_twenty_four_steps_exercised_when_all_are_evidenced():
    report = generate_report(official_runs(), _full_evidence())
    assert report.total_steps == 24
    assert report.exercised_count == 24
    assert report.not_exercised_count == 0
    assert all(line.status == "exercised" for line in report.lines)


def test_refusal_path_never_marks_a_step_exercised_without_evidence():
    evidence = _full_evidence()
    withheld_step_id = evidence[0].step_id
    evidence_missing_one = [e for e in evidence if e.step_id != withheld_step_id]

    report = generate_report(official_runs(), evidence_missing_one)

    withheld_line = next(line for line in report.lines if line.step_id == withheld_step_id)
    assert withheld_line.status == "not_exercised"
    assert "evidence" in withheld_line.reason
    assert report.exercised_count == 23
    assert report.not_exercised_count == 1


def test_a_step_never_performed_at_all_is_not_exercised_regardless_of_evidence():
    runs = official_runs()
    performed_step_ids = {a.step_id for run in runs for a in run.actions}
    all_step_ids = {s.step_id for s in all_steps()}
    assert performed_step_ids == all_step_ids  # sanity: the fixture covers all 24

    from dataclasses import replace

    truncated_first_run = replace(runs[0], actions=runs[0].actions[:1])
    runs_with_one_step_dropped = [truncated_first_run] + runs[1:]

    report = generate_report(runs_with_one_step_dropped, _full_evidence())
    dropped_step_ids = {a.step_id for a in runs[0].actions[1:]}
    for line in report.lines:
        if line.step_id in dropped_step_ids:
            assert line.status == "not_exercised"
            assert "not performed" in line.reason


def test_report_covers_exactly_the_twenty_four_named_playbook_steps():
    report = generate_report(official_runs(), _full_evidence())
    step_ids = {line.step_id for line in report.lines}
    assert step_ids == {s.step_id for s in all_steps()}
