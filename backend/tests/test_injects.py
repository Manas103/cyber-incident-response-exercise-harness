from incident_harness.injects import INJECTS, injects_for_scenario
from incident_harness.scenarios import SCENARIOS


def test_exactly_thirty_injects_total():
    assert len(INJECTS) == 30


def test_exactly_five_injects_per_scenario():
    for scenario in SCENARIOS:
        assert len(injects_for_scenario(scenario.scenario_id)) == 5


def test_inject_ids_are_unique():
    ids = [i.inject_id for i in INJECTS]
    assert len(ids) == len(set(ids))


def test_injects_are_ordered_by_increasing_timestamp_within_a_scenario():
    for scenario in SCENARIOS:
        timestamps = [i.timestamp_minutes for i in injects_for_scenario(scenario.scenario_id)]
        assert timestamps == sorted(timestamps)
        assert len(set(timestamps)) == len(timestamps)


def test_every_inject_references_a_real_scenario():
    scenario_ids = {s.scenario_id for s in SCENARIOS}
    for inject in INJECTS:
        assert inject.scenario_id in scenario_ids
