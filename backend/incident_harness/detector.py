"""The primary deviation detector: compares one run's actual responder
action log against its scenario's written playbook and names every
deviation (which step, which inject, which kind).

Implementation note (for the reference-oracle diff in
reference_detector.py): this version is dict/set based, O(steps +
actions). ActionRecord.step_id is the playbook step an action fulfills,
or None when the action does not match any step of the run's own
scenario (a "wrong step" candidate: either an unrecognized action, or
one that names a step belonging to a *different* scenario, which is
exactly how the seeded wrong_step fixture in fixtures.py is built)."""

from dataclasses import dataclass

from .scenarios import STEP_BY_ID, steps_for_scenario

DEVIATION_MISSING_STEP = "missing_step"
DEVIATION_WRONG_STEP = "wrong_step"
DEVIATION_OUT_OF_ORDER = "out_of_order"


@dataclass(frozen=True)
class ActionRecord:
    action_name: str
    timestamp_minutes: int
    step_id: str | None  # None or a step_id foreign to this run's scenario


@dataclass(frozen=True)
class Deviation:
    run_id: str
    inject_id: str
    scenario_id: str
    step_id: str
    step_name: str
    deviation_type: str
    detail: str

    def label(self) -> str:
        return f"{self.inject_id}/{self.step_id}: {self.deviation_type}"


def detect_deviations(
    run_id: str, inject_id: str, scenario_id: str, actions: list[ActionRecord]
) -> list[Deviation]:
    expected_steps = steps_for_scenario(scenario_id)
    expected_ids = {step.step_id for step in expected_steps}

    # Earliest matching action per expected step, and every action that
    # does not belong to this scenario's playbook at all.
    earliest_by_step: dict[str, ActionRecord] = {}
    foreign_actions: list[ActionRecord] = []
    for action in actions:
        if action.step_id is not None and action.step_id in expected_ids:
            current = earliest_by_step.get(action.step_id)
            if current is None or action.timestamp_minutes < current.timestamp_minutes:
                earliest_by_step[action.step_id] = action
        else:
            foreign_actions.append(action)

    deviations: list[Deviation] = []

    # Missing: an expected step with no matching action at all.
    for step in expected_steps:
        if step.step_id not in earliest_by_step:
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

    # Wrong step: an action logged for this run that does not belong to
    # this scenario's own playbook (an unrecognized action, or one that
    # names a step foreign to this scenario).
    for action in foreign_actions:
        foreign_step = STEP_BY_ID.get(action.step_id) if action.step_id else None
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

    # Out of order: every expected step is present, but the timestamps of
    # the matching actions are not monotonically increasing with the
    # playbook's own order_index.
    present_steps = [step for step in expected_steps if step.step_id in earliest_by_step]
    for earlier, later in zip(present_steps, present_steps[1:]):
        earlier_ts = earliest_by_step[earlier.step_id].timestamp_minutes
        later_ts = earliest_by_step[later.step_id].timestamp_minutes
        if later_ts < earlier_ts:
            deviations.append(
                Deviation(
                    run_id=run_id,
                    inject_id=inject_id,
                    scenario_id=scenario_id,
                    step_id=later.step_id,
                    step_name=later.name,
                    deviation_type=DEVIATION_OUT_OF_ORDER,
                    detail=(
                        f"step '{later.name}' ({later.phase}) logged at t={later_ts} before "
                        f"step '{earlier.name}' ({earlier.phase}) logged at t={earlier_ts}"
                    ),
                )
            )

    return deviations
