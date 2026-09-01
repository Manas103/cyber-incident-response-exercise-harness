"""Seeded, deterministic exercise fixtures with known ground truth, used
by the reference-oracle diff test, the seeded-deviation recall and
false-flag benchmarks, and the after-action-report tests.

Two fixtures matter here:

- `seeded_deviation_runs()`: exactly 40 runs, each carrying exactly one
  deliberately seeded deviation of a known type and step (missing_step,
  wrong_step, or out_of_order), built so that seeding one deviation
  never accidentally introduces a second one (see the module docstring
  notes on each builder below for why).
- `clean_runs()`: exactly 40 runs that exactly match their scenario's
  playbook, used to measure the false-flag rate.

Nothing here touches the database; these are plain dataclasses, exactly
like ai-governance-audit-readiness-register's generator.py."""

from dataclasses import dataclass

from .detector import DEVIATION_MISSING_STEP, DEVIATION_OUT_OF_ORDER, DEVIATION_WRONG_STEP, ActionRecord
from .injects import INJECTS, InjectDef
from .scenarios import SCENARIOS, ScenarioDef, steps_for_scenario

# Standard offsets (minutes after the inject) at which a compliant
# responder logs each phase; strictly increasing, so a clean run is
# never accidentally out of order and every action happens after its
# inject (time-to-detect / time-to-contain are never negative).
_PHASE_OFFSETS = {"detect": 5, "contain": 15, "eradicate": 30, "recover": 50}


@dataclass(frozen=True)
class RunRecordDef:
    run_id: str
    inject_id: str
    scenario_id: str
    kind: str  # "clean", "seeded_deviation", or "official"
    actions: tuple[ActionRecord, ...]


@dataclass(frozen=True)
class SeededDeviationCase:
    run: RunRecordDef
    expected_deviation_type: str
    expected_step_id: str
    expected_step_name: str


def _clean_actions(scenario_id: str, inject: InjectDef) -> list[ActionRecord]:
    actions = []
    for step in steps_for_scenario(scenario_id):
        offset = _PHASE_OFFSETS[step.phase]
        actions.append(
            ActionRecord(
                action_name=f"executed: {step.name}",
                timestamp_minutes=inject.timestamp_minutes + offset,
                step_id=step.step_id,
            )
        )
    return actions


def clean_runs(count: int = 40) -> list[RunRecordDef]:
    runs = []
    for i in range(count):
        inject = INJECTS[i % len(INJECTS)]
        actions = _clean_actions(inject.scenario_id, inject)
        runs.append(
            RunRecordDef(
                run_id=f"clean.{i:03d}",
                inject_id=inject.inject_id,
                scenario_id=inject.scenario_id,
                kind="clean",
                actions=tuple(actions),
            )
        )
    return runs


def _seed_missing_step(i: int, inject: InjectDef) -> SeededDeviationCase:
    """Drop exactly one required action. The other 3 stay correct and in
    their original relative order, so this never also trips an
    out_of_order or wrong_step flag."""
    steps = steps_for_scenario(inject.scenario_id)
    corrupt_index = i % len(steps)
    victim_step = steps[corrupt_index]
    actions = [a for a in _clean_actions(inject.scenario_id, inject) if a.step_id != victim_step.step_id]
    run = RunRecordDef(
        run_id=f"seeded.{i:03d}",
        inject_id=inject.inject_id,
        scenario_id=inject.scenario_id,
        kind="seeded_deviation",
        actions=tuple(actions),
    )
    return SeededDeviationCase(
        run=run,
        expected_deviation_type=DEVIATION_MISSING_STEP,
        expected_step_id=victim_step.step_id,
        expected_step_name=victim_step.name,
    )


def _seed_wrong_step(i: int, inject: InjectDef) -> SeededDeviationCase:
    """Keep all 4 correct actions (so nothing is missing and nothing is
    reordered) and add one extra action that names a step from a
    different scenario's playbook entirely, exactly the "wrong step"
    shape detector.py looks for."""
    steps = steps_for_scenario(inject.scenario_id)
    scenario_index = next(idx for idx, s in enumerate(SCENARIOS) if s.scenario_id == inject.scenario_id)
    # offset is always in 1..len(SCENARIOS)-1, so the foreign scenario is
    # never accidentally the run's own scenario (which would make the
    # "extra" action indistinguishable from a legitimate one).
    offset = 1 + (i // 3) % (len(SCENARIOS) - 1)
    foreign_scenario: ScenarioDef = SCENARIOS[(scenario_index + offset) % len(SCENARIOS)]
    foreign_phase_index = i % len(steps)
    foreign_step = foreign_scenario.steps[foreign_phase_index]

    actions = _clean_actions(inject.scenario_id, inject)
    extra_timestamp = actions[foreign_phase_index].timestamp_minutes + 2
    actions.append(
        ActionRecord(
            action_name=f"executed (mistakenly): {foreign_step.name}",
            timestamp_minutes=extra_timestamp,
            step_id=foreign_step.step_id,
        )
    )
    run = RunRecordDef(
        run_id=f"seeded.{i:03d}",
        inject_id=inject.inject_id,
        scenario_id=inject.scenario_id,
        kind="seeded_deviation",
        actions=tuple(actions),
    )
    return SeededDeviationCase(
        run=run,
        expected_deviation_type=DEVIATION_WRONG_STEP,
        expected_step_id=foreign_step.step_id,
        expected_step_name=foreign_step.name,
    )


def _seed_out_of_order(i: int, inject: InjectDef) -> SeededDeviationCase:
    """Keep all 4 correct step_ids but swap the timestamps of one
    adjacent pair of steps, so the actions are complete and correctly
    identified but logged in the wrong order."""
    steps = steps_for_scenario(inject.scenario_id)
    pair_index = i % (len(steps) - 1)
    actions = _clean_actions(inject.scenario_id, inject)
    actions[pair_index], actions[pair_index + 1] = (
        ActionRecord(
            action_name=actions[pair_index].action_name,
            timestamp_minutes=actions[pair_index + 1].timestamp_minutes,
            step_id=actions[pair_index].step_id,
        ),
        ActionRecord(
            action_name=actions[pair_index + 1].action_name,
            timestamp_minutes=actions[pair_index].timestamp_minutes,
            step_id=actions[pair_index + 1].step_id,
        ),
    )
    later_step = steps[pair_index + 1]
    run = RunRecordDef(
        run_id=f"seeded.{i:03d}",
        inject_id=inject.inject_id,
        scenario_id=inject.scenario_id,
        kind="seeded_deviation",
        actions=tuple(actions),
    )
    return SeededDeviationCase(
        run=run,
        expected_deviation_type=DEVIATION_OUT_OF_ORDER,
        expected_step_id=later_step.step_id,
        expected_step_name=later_step.name,
    )


_SEED_BUILDERS = (_seed_missing_step, _seed_wrong_step, _seed_out_of_order)


def seeded_deviation_runs(count: int = 40) -> list[SeededDeviationCase]:
    cases = []
    for i in range(count):
        inject = INJECTS[i % len(INJECTS)]
        builder = _SEED_BUILDERS[i % len(_SEED_BUILDERS)]
        cases.append(builder(i, inject))
    return cases


def official_runs() -> list[RunRecordDef]:
    """One designated, fully compliant run per scenario (6 total,
    covering all 24 playbook steps between them), used as the exercise
    record the after-action report and the console are built from."""
    runs = []
    for scenario in SCENARIOS:
        inject = next(i for i in INJECTS if i.scenario_id == scenario.scenario_id)
        actions = _clean_actions(scenario.scenario_id, inject)
        runs.append(
            RunRecordDef(
                run_id=f"official.{scenario.scenario_id}",
                inject_id=inject.inject_id,
                scenario_id=scenario.scenario_id,
                kind="official",
                actions=tuple(actions),
            )
        )
    return runs
