"""Invariant checks and the two headline correctness claims: every
flagged deviation names a real inject/step; timing is never negative
and never references an action that did not happen; 40/40 seeded
deviations recalled by name; 0 false flags over 40 clean runs."""

from incident_harness.detector import detect_deviations
from incident_harness.fixtures import clean_runs, seeded_deviation_runs
from incident_harness.injects import INJECT_BY_ID
from incident_harness.scenarios import STEP_BY_ID
from incident_harness.timing import compute_timing


def test_every_flagged_deviation_names_a_real_inject_and_step_across_all_seeded_runs():
    for case in seeded_deviation_runs(40):
        run = case.run
        for deviation in detect_deviations(run.run_id, run.inject_id, run.scenario_id, list(run.actions)):
            assert deviation.inject_id in INJECT_BY_ID
            assert deviation.step_id == "unrecognized" or deviation.step_id in STEP_BY_ID


def test_timing_is_never_negative_and_never_references_a_nonexistent_action_across_all_runs():
    all_runs = [c.run for c in seeded_deviation_runs(40)] + clean_runs(40)
    for run in all_runs:
        inject = INJECT_BY_ID[run.inject_id]
        timing = compute_timing(inject, list(run.actions))
        action_timestamps = {a.timestamp_minutes for a in run.actions}
        if timing.time_to_detect_minutes is not None:
            assert timing.time_to_detect_minutes >= 0
            assert (inject.timestamp_minutes + timing.time_to_detect_minutes) in action_timestamps
        if timing.time_to_contain_minutes is not None:
            assert timing.time_to_contain_minutes >= 0
            assert (inject.timestamp_minutes + timing.time_to_contain_minutes) in action_timestamps


def test_forty_of_forty_seeded_deviations_are_flagged_by_name():
    cases = seeded_deviation_runs(40)
    assert len(cases) == 40
    correctly_flagged = 0
    for case in cases:
        run = case.run
        found = detect_deviations(run.run_id, run.inject_id, run.scenario_id, list(run.actions))
        matches = [
            d
            for d in found
            if d.deviation_type == case.expected_deviation_type and d.step_id == case.expected_step_id
        ]
        if len(found) == 1 and len(matches) == 1:
            correctly_flagged += 1
    assert correctly_flagged == 40


def test_zero_false_flags_over_forty_clean_runs():
    runs = clean_runs(40)
    assert len(runs) == 40
    false_flags = 0
    for run in runs:
        found = detect_deviations(run.run_id, run.inject_id, run.scenario_id, list(run.actions))
        false_flags += len(found)
    assert false_flags == 0
