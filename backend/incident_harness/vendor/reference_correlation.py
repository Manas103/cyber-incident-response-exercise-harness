"""Independent oracle for correlate_vendor_alerts: a disjoint-set (union-find with
path compression) over the same pairwise entity-and-time test, rather than
correlation.py's adjacency-list BFS, and its own independently written aggregation
step. Shares no helper function with correlation.py, only the frozen
VendorAlert/VendorIncident dataclass shapes and the window constant, which are the
written specification both implementations are independently built from, not
shared code."""

from __future__ import annotations

from .correlation import CORRELATION_WINDOW_MINUTES, VendorIncident
from .feeds import VendorAlert

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


def _aggregate_reference(members: list[VendorAlert]) -> VendorIncident:
    """A deliberately different traversal shape from correlation.py's _aggregate:
    single pass accumulating running maxima instead of two separate max() calls."""
    worst_sensitivity_rank = -1
    worst_sensitivity = None
    worst_scope_rank = -1
    worst_scope = None
    exploited = False
    entity_set = set()
    feed_set = set()
    earliest = None
    latest = None
    for member in members:
        if _SENSITIVITY_RANK[member.data_sensitivity] > worst_sensitivity_rank:
            worst_sensitivity_rank = _SENSITIVITY_RANK[member.data_sensitivity]
            worst_sensitivity = member.data_sensitivity
        if _SCOPE_RANK[member.scope] > worst_scope_rank:
            worst_scope_rank = _SCOPE_RANK[member.scope]
            worst_scope = member.scope
        exploited = exploited or member.actively_exploited
        entity_set.update(member.entities)
        feed_set.add(member.feed)
        if earliest is None or member.timestamp_minutes < earliest:
            earliest = member.timestamp_minutes
        if latest is None or member.timestamp_minutes > latest:
            latest = member.timestamp_minutes

    alert_ids = tuple(sorted(m.alert_id for m in members))
    return VendorIncident(
        incident_id="VINC-" + "-".join(alert_ids),
        alert_ids=alert_ids,
        feeds=tuple(sorted(feed_set)),
        entities=tuple(sorted(entity_set)),
        start_minutes=earliest,
        end_minutes=latest,
        data_sensitivity=worst_sensitivity,
        scope=worst_scope,
        actively_exploited=exploited,
    )


class _DisjointSet:
    def __init__(self, items: list[str]):
        self._parent = {item: item for item in items}

    def find(self, item: str) -> str:
        root = item
        while self._parent[root] != root:
            root = self._parent[root]
        while self._parent[item] != root:
            self._parent[item], item = root, self._parent[item]
        return root

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self._parent[ra] = rb


def _linked_reference(a: VendorAlert, b: VendorAlert) -> bool:
    within_window = abs(a.timestamp_minutes - b.timestamp_minutes) <= CORRELATION_WINDOW_MINUTES
    shares_entity = False
    for entity in a.entities:
        if entity in b.entities:
            shares_entity = True
            break
    return within_window and shares_entity


def correlate_vendor_alerts_reference(alerts: list[VendorAlert]) -> list[VendorIncident]:
    ids = [a.alert_id for a in alerts]
    ds = _DisjointSet(ids)
    for i in range(len(alerts)):
        for j in range(i + 1, len(alerts)):
            if _linked_reference(alerts[i], alerts[j]):
                ds.union(alerts[i].alert_id, alerts[j].alert_id)

    groups: dict[str, list[VendorAlert]] = {}
    for alert in alerts:
        root = ds.find(alert.alert_id)
        groups.setdefault(root, []).append(alert)

    incidents = [_aggregate_reference(members) for members in groups.values()]
    incidents.sort(key=lambda inc: inc.start_minutes)
    return incidents
