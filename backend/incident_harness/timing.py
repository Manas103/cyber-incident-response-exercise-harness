"""Time-to-detect and time-to-contain, computed per inject against the
written playbook: the first responder action matching the scenario's
own "detect" (or "contain") step, minus the inject's own timestamp.

Both are None, not zero and not a negative number, when no matching
action exists in the run at all (for example, a run carrying a
seeded missing_step deviation on the detect or contain step). Never
negative: a well-formed run's actions never occur before the inject
that triggered them, which fixtures.py enforces at generation time and
tests/test_invariants.py checks structurally rather than assuming."""

from dataclasses import dataclass

from .detector import ActionRecord
from .injects import InjectDef
from .scenarios import step_for_phase


@dataclass(frozen=True)
class InjectTiming:
    inject_id: str
    scenario_id: str
    time_to_detect_minutes: int | None
    time_to_contain_minutes: int | None


def _earliest_for_phase(scenario_id: str, phase: str, actions: list[ActionRecord]) -> ActionRecord | None:
    step = step_for_phase(scenario_id, phase)
    matching = [a for a in actions if a.step_id == step.step_id]
    if not matching:
        return None
    return min(matching, key=lambda a: a.timestamp_minutes)


def compute_timing(inject: InjectDef, actions: list[ActionRecord]) -> InjectTiming:
    detect_action = _earliest_for_phase(inject.scenario_id, "detect", actions)
    contain_action = _earliest_for_phase(inject.scenario_id, "contain", actions)

    time_to_detect = (
        detect_action.timestamp_minutes - inject.timestamp_minutes if detect_action is not None else None
    )
    time_to_contain = (
        contain_action.timestamp_minutes - inject.timestamp_minutes if contain_action is not None else None
    )

    return InjectTiming(
        inject_id=inject.inject_id,
        scenario_id=inject.scenario_id,
        time_to_detect_minutes=time_to_detect,
        time_to_contain_minutes=time_to_contain,
    )
