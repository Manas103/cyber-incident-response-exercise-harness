from incident_harness.vendor.containment import (
    ContainmentRequest,
    EntityStateStore,
    STATE_NORMAL,
    apply_containment,
    undo_containment,
)
from incident_harness.vendor.fixtures import build_containment_gate_cases

N_EACH = 50  # 50 unapproved + 50 approved = 100 gate decisions


def test_gate_decisions_all_correct_and_nothing_unapproved_executes():
    cases = build_containment_gate_cases(N_EACH, seed=20261116)
    store = EntityStateStore()

    correct = 0
    unapproved_executed = 0
    for case in cases:
        result = apply_containment(case.request, store)
        if result.executed == case.expect_executed:
            correct += 1
        if case.request.approved_by is None and result.executed:
            unapproved_executed += 1
        if not case.expect_executed:
            assert store.state_of(case.request.target_entity) == STATE_NORMAL

    assert correct == len(cases) == 2 * N_EACH
    assert unapproved_executed == 0


def test_every_executed_action_is_reversible():
    cases = build_containment_gate_cases(N_EACH, seed=20261116)
    store = EntityStateStore()
    executed = []
    for case in cases:
        result = apply_containment(case.request, store)
        if result.executed:
            executed.append((case.request, result))

    assert len(executed) == N_EACH

    reverted = 0
    for request, result in executed:
        before_undo = store.state_of(request.target_entity)
        assert before_undo == result.state_after
        undo = undo_containment(request, result, store)
        after_undo = store.state_of(request.target_entity)
        assert after_undo == result.state_before == STATE_NORMAL
        assert undo.undone
        reverted += 1

    assert reverted == N_EACH == len(executed)


def test_a_refused_request_leaves_nothing_to_undo():
    cases = build_containment_gate_cases(1, seed=1)
    unapproved_case = next(c for c in cases if not c.expect_executed)
    store = EntityStateStore()
    result = apply_containment(unapproved_case.request, store)
    assert not result.executed
    assert result.state_before == result.state_after == STATE_NORMAL
