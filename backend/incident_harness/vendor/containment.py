"""Executable containment actions, generalizing intake/notification.py's named-human-
approval gate from "hold a message" to "change the state of a live host, session or
credential". Three action types: host isolation, session revoke, token reset. Every
apply is refused outright, with nothing executed, unless approved_by names a real
person; every action that does execute is recorded with enough state to be undone
exactly, because containment during a trading day is not a free action and a wrong
call has to be reversible, not just loggable."""

from __future__ import annotations

from dataclasses import dataclass, field

ACTION_HOST_ISOLATION = "host_isolation"
ACTION_SESSION_REVOKE = "session_revoke"
ACTION_TOKEN_RESET = "token_reset"

STATE_NORMAL = "normal"
STATE_ISOLATED = "isolated"
STATE_SESSION_REVOKED = "session_revoked"
STATE_TOKEN_RESET = "token_reset"

_ACTION_STATE = {
    ACTION_HOST_ISOLATION: STATE_ISOLATED,
    ACTION_SESSION_REVOKE: STATE_SESSION_REVOKED,
    ACTION_TOKEN_RESET: STATE_TOKEN_RESET,
}


def state_for_action(action_type: str) -> str:
    """The state an action type puts its target into if it executes; the one
    piece of _ACTION_STATE the API layer needs without reaching into a
    module-private dict."""
    return _ACTION_STATE[action_type]


@dataclass(frozen=True)
class ContainmentRequest:
    action_id: str
    incident_id: str
    action_type: str
    target_entity: str
    action_minutes: int
    approved_by: str | None = None


@dataclass(frozen=True)
class ContainmentResult:
    action_id: str
    executed: bool
    reason: str
    approved_by: str | None
    state_before: str | None
    state_after: str | None


@dataclass(frozen=True)
class UndoResult:
    action_id: str
    undone: bool
    reason: str
    state_before: str
    state_after: str


@dataclass
class EntityStateStore:
    """Tracks each target entity's current containment state. A real deployment
    would read this from the EDR/IdP/SOAR platform itself; this in-memory store
    stands in for that, exactly as device-telemetry-policy-middleware's policy
    plane stands in for a live vendor API."""

    _states: dict[str, str] = field(default_factory=dict)
    _history: dict[str, list[str]] = field(default_factory=dict)

    def state_of(self, target_entity: str) -> str:
        return self._states.get(target_entity, STATE_NORMAL)

    def _set(self, target_entity: str, state: str) -> None:
        self._history.setdefault(target_entity, []).append(self.state_of(target_entity))
        self._states[target_entity] = state

    def _pop_previous(self, target_entity: str) -> str:
        history = self._history.get(target_entity, [])
        if not history:
            return STATE_NORMAL
        return history.pop()


def apply_containment(request: ContainmentRequest, store: EntityStateStore) -> ContainmentResult:
    approver = (request.approved_by or "").strip()
    state_before = store.state_of(request.target_entity)
    if not approver:
        return ContainmentResult(
            action_id=request.action_id,
            executed=False,
            reason="no named human approval",
            approved_by=None,
            state_before=state_before,
            state_after=state_before,
        )
    new_state = _ACTION_STATE[request.action_type]
    store._set(request.target_entity, new_state)
    return ContainmentResult(
        action_id=request.action_id,
        executed=True,
        reason=f"approved by {approver}",
        approved_by=approver,
        state_before=state_before,
        state_after=new_state,
    )


def undo_containment(request: ContainmentRequest, result: ContainmentResult, store: EntityStateStore) -> UndoResult:
    """Only ever called for a result that actually executed; undoing a refused
    request is a no-op by construction (there is nothing to undo), checked in
    tests/test_vendor_containment_gate.py rather than assumed here."""
    current = store.state_of(request.target_entity)
    restored = store._pop_previous(request.target_entity)
    store._states[request.target_entity] = restored
    return UndoResult(
        action_id=request.action_id,
        undone=True,
        reason=f"reverted {request.target_entity} from {current} to {restored}",
        state_before=current,
        state_after=restored,
    )
