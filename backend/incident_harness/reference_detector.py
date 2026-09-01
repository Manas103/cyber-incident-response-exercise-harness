"""An independent, deliberately differently-shaped reimplementation of
detect_deviations, used only to diff against detector.py in
tests/test_reference_oracle_diff.py.

This is not detector.py with variables renamed. It never builds a
dict or a set: every lookup is a manual linear (or, for the ordering
check, quadratic) scan over plain lists, and the ordering check uses a
different logical test (every earlier-order step compared against
every later-order step, not just adjacent pairs) to reach the same
conclusion by a different route."""

from .detector import (
    DEVIATION_MISSING_STEP,
    DEVIATION_OUT_OF_ORDER,
    DEVIATION_WRONG_STEP,
    ActionRecord,
    Deviation,
)
from .scenarios import all_steps, steps_for_scenario


def _find_step_by_id(step_id: str):
    for step in all_steps():
        if step.step_id == step_id:
            return step
    return None


def _earliest_timestamp_for_step(step_id: str, actions: list[ActionRecord]) -> int | None:
    earliest: int | None = None
    for action in actions:
        if action.step_id == step_id:
            if earliest is None or action.timestamp_minutes < earliest:
                earliest = action.timestamp_minutes
    return earliest


def _is_expected_step(step_id: str | None, expected_steps) -> bool:
    if step_id is None:
        return False
    for step in expected_steps:
        if step.step_id == step_id:
            return True
    return False


def detect_deviations_reference(
    run_id: str, inject_id: str, scenario_id: str, actions: list[ActionRecord]
) -> list[Deviation]:
    expected_steps = list(steps_for_scenario(scenario_id))

    deviations: list[Deviation] = []

    # Missing: walk the ordered expected step list once, scanning the
    # full action list by hand for each one (no dict).
    found_timestamp: list[int | None] = []
    for step in expected_steps:
        ts = _earliest_timestamp_for_step(step.step_id, actions)
        found_timestamp.append(ts)
        if ts is None:
            deviations.append(
                Deviation(
                    run_id=run_id,
                    inject_id=inject_id,
                    scenario_id=scenario_id,
                    step_id=step.step_id,
                    step_name=step.name,
                    deviation_type=DEVIATION_MISSING_STEP,
                    detail=f"expected step '{step.name}' ({step.phase}) has no matching responder action",
                )
            )

    # Wrong step: walk the raw action list; an action counts as foreign
    # if a manual scan of expected_steps never matches its step_id.
    for action in actions:
        if _is_expected_step(action.step_id, expected_steps):
            continue
        foreign_step = _find_step_by_id(action.step_id) if action.step_id else None
        if foreign_step is not None:
            detail = (
                f"action '{action.action_name}' logged against foreign step "
                f"'{foreign_step.name}' ({foreign_step.scenario_id}), which is not part of "
                f"this run's own playbook"
            )
            step_name = foreign_step.name
        else:
            detail = f"action '{action.action_name}' does not match any step of this run's playbook"
            step_name = action.action_name
        deviations.append(
            Deviation(
                run_id=run_id,
                inject_id=inject_id,
                scenario_id=scenario_id,
                step_id=action.step_id or "unrecognized",
                step_name=step_name,
                deviation_type=DEVIATION_WRONG_STEP,
                detail=detail,
            )
        )

    # Out of order: quadratic pairwise scan. For every present step,
    # count how many *earlier-in-the-playbook* steps have a strictly
    # later timestamp; if any do, this step is out of order relative to
    # the playbook, flagged once at this step.
    for later_index in range(len(expected_steps)):
        later_ts = found_timestamp[later_index]
        if later_ts is None:
            continue
        violated = False
        for earlier_index in range(later_index):
            earlier_ts = found_timestamp[earlier_index]
            if earlier_ts is not None and earlier_ts > later_ts:
                violated = True
        if violated:
            later_step = expected_steps[later_index]
            # Name the nearest preceding present step for the detail
            # message, matching detector.py's adjacent-pair phrasing.
            nearest_earlier_index = later_index - 1
            while nearest_earlier_index >= 0 and found_timestamp[nearest_earlier_index] is None:
                nearest_earlier_index -= 1
            if nearest_earlier_index >= 0:
                earlier_step = expected_steps[nearest_earlier_index]
                earlier_ts = found_timestamp[nearest_earlier_index]
                detail = (
                    f"step '{later_step.name}' ({later_step.phase}) logged at t={later_ts} before "
                    f"step '{earlier_step.name}' ({earlier_step.phase}) logged at t={earlier_ts}"
                )
            else:
                detail = f"step '{later_step.name}' ({later_step.phase}) logged out of playbook order"
            deviations.append(
                Deviation(
                    run_id=run_id,
                    inject_id=inject_id,
                    scenario_id=scenario_id,
                    step_id=later_step.step_id,
                    step_name=later_step.name,
                    deviation_type=DEVIATION_OUT_OF_ORDER,
                    detail=detail,
                )
            )

    return deviations
