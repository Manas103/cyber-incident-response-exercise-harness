from incident_harness.scenarios import PHASES, SCENARIOS, all_steps


def test_exactly_six_scenarios():
    assert len(SCENARIOS) == 6


def test_each_scenario_has_exactly_four_steps_one_per_phase():
    for scenario in SCENARIOS:
        assert len(scenario.steps) == 4
        assert tuple(step.phase for step in scenario.steps) == PHASES


def test_exactly_twenty_four_named_playbook_steps_total():
    steps = all_steps()
    assert len(steps) == 24
    assert len(set(step.step_id for step in steps)) == 24


def test_every_step_has_a_nonempty_name():
    for step in all_steps():
        assert step.name.strip() != ""


def test_step_order_index_matches_phase_position():
    for scenario in SCENARIOS:
        for index, step in enumerate(scenario.steps):
            assert step.order_index == index
