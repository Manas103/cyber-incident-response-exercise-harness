"""Computes VendorIncidentTiming against the written playbook in playbook.py.
Mirrors the structure of the tabletop timing.py (earliest matching action minus
the trigger timestamp, None rather than 0 or negative when no match exists) but
is a separate, smaller function because the trigger here is an incident's
earliest correlated alert, not a scenario's own inject definition."""

from __future__ import annotations

from .correlation import VendorIncident
from .playbook import VendorIncidentTiming


def compute_vendor_timing(
    incident: VendorIncident,
    ack_minutes: int | None,
    first_executed_contain_minutes: int | None,
) -> VendorIncidentTiming:
    time_to_detect = ack_minutes - incident.start_minutes if ack_minutes is not None else None
    time_to_contain = (
        first_executed_contain_minutes - incident.start_minutes
        if first_executed_contain_minutes is not None
        else None
    )
    return VendorIncidentTiming(
        incident_id=incident.incident_id,
        time_to_detect_minutes=time_to_detect,
        time_to_contain_minutes=time_to_contain,
    )
