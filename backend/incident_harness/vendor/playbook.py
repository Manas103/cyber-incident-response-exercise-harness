"""The written playbook time-to-detect and time-to-contain are scored against,
for a vendor-sourced incident (as distinct from timing.py's scenario/inject
playbook, which scores a tabletop exercise run against a fixed per-scenario step
list). Written down once, in plain language, the same reason severity.py's
MATRIX_RULES and the tabletop playbook's steps are both spelled out rather than
left implicit:

  Detect step: an analyst must log an acknowledgment against the incident
  (any named analyst, any time after the earliest correlated alert). Time-to-
  detect is that acknowledgment's timestamp minus the incident's earliest
  alert timestamp.

  Contain step: the first containment action that actually executed (i.e. was
  approved, see containment.py) against any entity in the incident. Time-to-
  contain is that action's timestamp minus the incident's earliest alert
  timestamp.

  Either metric is None, not zero, when the corresponding step never happened
  in the record at all (no ack logged; no containment action executed)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VendorIncidentTiming:
    incident_id: str
    time_to_detect_minutes: int | None
    time_to_contain_minutes: int | None
