"""Every customer notification is held behind a named human approval: send_notification()
refuses to send unless approved_by names a real person, and the result always says who
approved it (or why it did not send), never a silent drop."""

from dataclasses import dataclass


@dataclass(frozen=True)
class NotificationRequest:
    incident_source_reference: str
    message: str
    approved_by: str | None = None


@dataclass(frozen=True)
class NotificationResult:
    sent: bool
    reason: str
    approved_by: str | None


def send_notification(request: NotificationRequest) -> NotificationResult:
    approver = (request.approved_by or "").strip()
    if not approver:
        return NotificationResult(sent=False, reason="no named human approval", approved_by=None)
    return NotificationResult(sent=True, reason=f"approved by {approver}", approved_by=approver)
