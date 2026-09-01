"""Hand-built micro examples, one per deviation type plus the clean
case, independent of the seeded fixtures in fixtures.py."""

from incident_harness.detector import (
    DEVIATION_MISSING_STEP,
    DEVIATION_OUT_OF_ORDER,
    DEVIATION_WRONG_STEP,
    ActionRecord,
    detect_deviations,
)


def _clean_actions():
    return [
        ActionRecord("detected", 5, "ransomware_corporate_it.detect"),
        ActionRecord("contained", 15, "ransomware_corporate_it.contain"),
        ActionRecord("eradicated", 30, "ransomware_corporate_it.eradicate"),
        ActionRecord("recovered", 50, "ransomware_corporate_it.recover"),
    ]


def test_clean_run_has_no_deviations():
    deviations = detect_deviations("r1", "ransomware_corporate_it.inject1", "ransomware_corporate_it", _clean_actions())
    assert deviations == []


def test_missing_step_is_flagged_by_name():
    actions = [a for a in _clean_actions() if a.step_id != "ransomware_corporate_it.contain"]
    deviations = detect_deviations("r2", "ransomware_corporate_it.inject1", "ransomware_corporate_it", actions)
    assert len(deviations) == 1
    assert deviations[0].deviation_type == DEVIATION_MISSING_STEP
    assert deviations[0].step_id == "ransomware_corporate_it.contain"


def test_wrong_step_extra_action_is_flagged_by_name():
    actions = _clean_actions() + [ActionRecord("mistaken", 12, "phishing_credential_compromise.contain")]
    deviations = detect_deviations("r3", "ransomware_corporate_it.inject1", "ransomware_corporate_it", actions)
    assert len(deviations) == 1
    assert deviations[0].deviation_type == DEVIATION_WRONG_STEP
    assert deviations[0].step_id == "phishing_credential_compromise.contain"


def test_unrecognized_action_with_no_step_id_is_flagged_as_wrong_step():
    actions = _clean_actions() + [ActionRecord("did something unrelated", 12, None)]
    deviations = detect_deviations("r4", "ransomware_corporate_it.inject1", "ransomware_corporate_it", actions)
    assert len(deviations) == 1
    assert deviations[0].deviation_type == DEVIATION_WRONG_STEP
    assert deviations[0].step_id == "unrecognized"


def test_out_of_order_is_flagged_naming_the_step_that_jumped_early():
    # eradicate (playbook position 2) is logged before contain (position
    # 1), which the playbook expects first; the step out of place is
    # eradicate, the one that ran ahead of turn.
    actions = [
        ActionRecord("detected", 5, "ransomware_corporate_it.detect"),
        ActionRecord("eradicated", 20, "ransomware_corporate_it.eradicate"),
        ActionRecord("contained", 30, "ransomware_corporate_it.contain"),
        ActionRecord("recovered", 50, "ransomware_corporate_it.recover"),
    ]
    deviations = detect_deviations("r5", "ransomware_corporate_it.inject1", "ransomware_corporate_it", actions)
    assert len(deviations) == 1
    assert deviations[0].deviation_type == DEVIATION_OUT_OF_ORDER
    assert deviations[0].step_id == "ransomware_corporate_it.eradicate"


def test_every_deviation_names_a_real_inject_and_step_that_exist():
    from incident_harness.injects import INJECT_BY_ID
    from incident_harness.scenarios import STEP_BY_ID

    actions = [a for a in _clean_actions() if a.step_id != "ransomware_corporate_it.recover"]
    deviations = detect_deviations("r6", "ransomware_corporate_it.inject3", "ransomware_corporate_it", actions)
    assert len(deviations) == 1
    assert deviations[0].inject_id in INJECT_BY_ID
    assert deviations[0].step_id in STEP_BY_ID
