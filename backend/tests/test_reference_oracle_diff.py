"""detect_deviations (dict/set based) diffed exactly against
detect_deviations_reference (linear/quadratic scan based, no dict or
set membership) over all 80 seeded fixture runs: the 40 seeded-deviation
runs and the 40 clean runs. Both must report exactly the same
(step_id, deviation_type) set for every run."""

from incident_harness.detector import detect_deviations
from incident_harness.fixtures import clean_runs, seeded_deviation_runs
from incident_harness.reference_detector import detect_deviations_reference


def _all_runs():
    return [c.run for c in seeded_deviation_runs(40)] + clean_runs(40)


def test_primary_and_reference_agree_exactly_on_every_seeded_and_clean_run():
    for run in _all_runs():
        primary = detect_deviations(run.run_id, run.inject_id, run.scenario_id, list(run.actions))
        reference = detect_deviations_reference(run.run_id, run.inject_id, run.scenario_id, list(run.actions))
        primary_set = {(d.step_id, d.deviation_type) for d in primary}
        reference_set = {(d.step_id, d.deviation_type) for d in reference}
        assert primary_set == reference_set, f"mismatch on {run.run_id}: {primary_set} != {reference_set}"


def test_reference_oracle_is_not_a_renamed_copy():
    """A structural guard: the reference module must not import or reuse
    detector.py's own detection functions, only its shared dataclasses."""
    import inspect

    from incident_harness import reference_detector

    source = inspect.getsource(reference_detector)
    assert "detect_deviations(" not in source
    assert "set(" not in source
    assert " in expected_ids" not in source
