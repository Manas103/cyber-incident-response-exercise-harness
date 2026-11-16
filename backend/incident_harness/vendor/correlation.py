"""Primary entity-and-time correlation engine: two alerts are linked when they
share at least one (entity_type, value) pair and land within
CORRELATION_WINDOW_MINUTES of each other; one incident is one connected component
of that graph. Built as an adjacency-list graph traversed by BFS. See
reference_correlation.py for the second, independently coded implementation
(disjoint-set/union-find over the same pairwise test) used as the oracle in
tests/test_vendor_correlation_oracle_diff.py."""

from __future__ import annotations

from dataclasses import dataclass

from .feeds import VendorAlert

CORRELATION_WINDOW_MINUTES = 120

_SENSITIVITY_RANK = {
    "none": 0,
    "internal_only": 1,
    "customer_pii": 2,
    "payment_or_credentials": 3,
}
_SCOPE_RANK = {
    "single_customer": 0,
    "multiple_customers": 1,
    "platform_wide": 2,
}


@dataclass(frozen=True)
class VendorIncident:
    incident_id: str
    alert_ids: tuple[str, ...]
    feeds: tuple[str, ...]
    entities: tuple[tuple[str, str], ...]
    start_minutes: int
    end_minutes: int
    data_sensitivity: str
    scope: str
    actively_exploited: bool

    def content_key(self):
        """Ignores the generated incident_id (the two engines name incidents
        differently); used to diff two incident sets for exact agreement."""
        return (
            tuple(sorted(self.alert_ids)),
            tuple(sorted(self.feeds)),
            tuple(sorted(self.entities)),
            self.start_minutes,
            self.end_minutes,
            self.data_sensitivity,
            self.scope,
            self.actively_exploited,
        )


def _linked(a: VendorAlert, b: VendorAlert) -> bool:
    if abs(a.timestamp_minutes - b.timestamp_minutes) > CORRELATION_WINDOW_MINUTES:
        return False
    return bool(set(a.entities) & set(b.entities))


def _aggregate(alerts: list[VendorAlert], alert_ids: tuple[str, ...]) -> VendorIncident:
    worst_sensitivity = max(alerts, key=lambda a: _SENSITIVITY_RANK[a.data_sensitivity]).data_sensitivity
    worst_scope = max(alerts, key=lambda a: _SCOPE_RANK[a.scope]).scope
    exploited = any(a.actively_exploited for a in alerts)
    entities = sorted({pair for a in alerts for pair in a.entities})
    feeds = sorted({a.feed for a in alerts})
    return VendorIncident(
        incident_id="VINC-" + "-".join(sorted(alert_ids)),
        alert_ids=tuple(sorted(alert_ids)),
        feeds=tuple(feeds),
        entities=tuple(entities),
        start_minutes=min(a.timestamp_minutes for a in alerts),
        end_minutes=max(a.timestamp_minutes for a in alerts),
        data_sensitivity=worst_sensitivity,
        scope=worst_scope,
        actively_exploited=exploited,
    )


def correlate_vendor_alerts(alerts: list[VendorAlert]) -> list[VendorIncident]:
    """BFS over an adjacency list built from every pairwise _linked() test."""
    by_id = {a.alert_id: a for a in alerts}
    adjacency: dict[str, set[str]] = {a.alert_id: set() for a in alerts}
    for i, a in enumerate(alerts):
        for b in alerts[i + 1 :]:
            if _linked(a, b):
                adjacency[a.alert_id].add(b.alert_id)
                adjacency[b.alert_id].add(a.alert_id)

    visited: set[str] = set()
    incidents: list[VendorIncident] = []
    for alert_id in sorted(adjacency):
        if alert_id in visited:
            continue
        component = []
        queue = [alert_id]
        visited.add(alert_id)
        while queue:
            current = queue.pop(0)
            component.append(current)
            for neighbor in sorted(adjacency[current]):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        component_alerts = [by_id[cid] for cid in component]
        incidents.append(_aggregate(component_alerts, tuple(component)))

    incidents.sort(key=lambda inc: inc.start_minutes)
    return incidents
