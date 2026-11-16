"""Registers the vendor-feed extension's routes: one ingest endpoint per feed,
a derived incidents listing (recomputed from stored alerts on every read, see
models.py), an analyst-acknowledgment endpoint for time-to-detect, and the
containment approval gate with its undo endpoint. Current containment state
per target_entity is derived from the ContainmentActionRow audit log rather
than kept in a separate mutable table, for the same reason incidents are
derived from alerts rather than stored: a stored "current state" column could
drift from the log that is supposed to explain it."""

import json

from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import Session, sessionmaker

from ..intake.severity import SeverityInputs, classify_severity
from .containment import ContainmentRequest, ContainmentResult, EntityStateStore, STATE_NORMAL, apply_containment, state_for_action, undo_containment
from .correlation import correlate_vendor_alerts
from .feeds import (
    EmailGatewayRaw,
    EndpointDetectionRaw,
    IdentityProviderRaw,
    ManagedDetectionEscalationRaw,
    VendorAlert,
    normalize_email_gateway,
    normalize_endpoint_detection,
    normalize_identity_provider,
    normalize_mdr_escalation,
)
from .models import AnalystAckRow, ContainmentActionRow, VendorAlertRow
from .schemas import (
    AcceptedOut,
    AnalystAckIn,
    ContainmentActionIn,
    ContainmentActionOut,
    EmailGatewayIn,
    EndpointDetectionIn,
    IdentityProviderIn,
    ManagedDetectionEscalationIn,
    UndoOut,
    VendorIncidentOut,
)
from .timing import compute_vendor_timing


def _persist_alert(session: Session, alert: VendorAlert) -> VendorAlertRow:
    row = VendorAlertRow(
        alert_id=alert.alert_id,
        feed=alert.feed,
        entities_json=json.dumps([list(pair) for pair in alert.entities]),
        summary=alert.summary,
        data_sensitivity=alert.data_sensitivity,
        scope=alert.scope,
        actively_exploited=alert.actively_exploited,
        timestamp_minutes=alert.timestamp_minutes,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _row_to_alert(row: VendorAlertRow) -> VendorAlert:
    return VendorAlert(
        alert_id=row.alert_id,
        feed=row.feed,
        entities=tuple(tuple(pair) for pair in json.loads(row.entities_json)),
        summary=row.summary,
        data_sensitivity=row.data_sensitivity,
        scope=row.scope,
        actively_exploited=row.actively_exploited,
        timestamp_minutes=row.timestamp_minutes,
    )


def _current_state_of_entity(session: Session, target_entity: str) -> str:
    row = (
        session.query(ContainmentActionRow)
        .filter(
            ContainmentActionRow.target_entity == target_entity,
            ContainmentActionRow.executed.is_(True),
            ContainmentActionRow.undone.is_(False),
        )
        .order_by(ContainmentActionRow.id.desc())
        .first()
    )
    if row is None:
        return STATE_NORMAL
    return state_for_action(row.action_type)


def register_vendor_routes(fastapi_app: FastAPI, session_factory: sessionmaker) -> None:
    @fastapi_app.post("/api/vendor-alerts/endpoint-detection", response_model=AcceptedOut)
    def ingest_endpoint_detection(payload: EndpointDetectionIn) -> AcceptedOut:
        session = session_factory()
        try:
            _persist_alert(session, normalize_endpoint_detection(EndpointDetectionRaw(**payload.model_dump())))
        finally:
            session.close()
        return AcceptedOut(accepted=True)

    @fastapi_app.post("/api/vendor-alerts/email-gateway", response_model=AcceptedOut)
    def ingest_email_gateway(payload: EmailGatewayIn) -> AcceptedOut:
        session = session_factory()
        try:
            _persist_alert(session, normalize_email_gateway(EmailGatewayRaw(**payload.model_dump())))
        finally:
            session.close()
        return AcceptedOut(accepted=True)

    @fastapi_app.post("/api/vendor-alerts/identity-provider", response_model=AcceptedOut)
    def ingest_identity_provider(payload: IdentityProviderIn) -> AcceptedOut:
        session = session_factory()
        try:
            _persist_alert(session, normalize_identity_provider(IdentityProviderRaw(**payload.model_dump())))
        finally:
            session.close()
        return AcceptedOut(accepted=True)

    @fastapi_app.post("/api/vendor-alerts/mdr-escalation", response_model=AcceptedOut)
    def ingest_mdr_escalation(payload: ManagedDetectionEscalationIn) -> AcceptedOut:
        session = session_factory()
        try:
            _persist_alert(session, normalize_mdr_escalation(ManagedDetectionEscalationRaw(**payload.model_dump())))
        finally:
            session.close()
        return AcceptedOut(accepted=True)

    @fastapi_app.get("/api/vendor-incidents", response_model=list[VendorIncidentOut])
    def list_vendor_incidents() -> list[VendorIncidentOut]:
        session = session_factory()
        try:
            alert_rows = session.query(VendorAlertRow).order_by(VendorAlertRow.id).all()
            alerts = [_row_to_alert(r) for r in alert_rows]
            incidents = correlate_vendor_alerts(alerts)

            out = []
            for incident in incidents:
                severity = classify_severity(
                    SeverityInputs(
                        data_sensitivity=incident.data_sensitivity,
                        scope=incident.scope,
                        actively_exploited=incident.actively_exploited,
                    )
                )
                ack = (
                    session.query(AnalystAckRow)
                    .filter(AnalystAckRow.incident_id == incident.incident_id)
                    .one_or_none()
                )
                first_contain = (
                    session.query(ContainmentActionRow)
                    .filter(
                        ContainmentActionRow.incident_id == incident.incident_id,
                        ContainmentActionRow.executed.is_(True),
                    )
                    .order_by(ContainmentActionRow.action_minutes)
                    .first()
                )
                timing = compute_vendor_timing(
                    incident,
                    ack_minutes=ack.ack_minutes if ack is not None else None,
                    first_executed_contain_minutes=first_contain.action_minutes if first_contain is not None else None,
                )
                out.append(
                    VendorIncidentOut(
                        incident_id=incident.incident_id,
                        alert_ids=list(incident.alert_ids),
                        feeds=list(incident.feeds),
                        entities=[list(pair) for pair in incident.entities],
                        start_minutes=incident.start_minutes,
                        end_minutes=incident.end_minutes,
                        data_sensitivity=incident.data_sensitivity,
                        scope=incident.scope,
                        actively_exploited=incident.actively_exploited,
                        severity=severity,
                        time_to_detect_minutes=timing.time_to_detect_minutes,
                        time_to_contain_minutes=timing.time_to_contain_minutes,
                    )
                )
            return out
        finally:
            session.close()

    @fastapi_app.post("/api/vendor-incidents/ack")
    def ack_incident(payload: AnalystAckIn):
        session = session_factory()
        try:
            existing = (
                session.query(AnalystAckRow).filter(AnalystAckRow.incident_id == payload.incident_id).one_or_none()
            )
            if existing is not None:
                raise HTTPException(status_code=409, detail="incident already acknowledged")
            session.add(
                AnalystAckRow(
                    incident_id=payload.incident_id,
                    analyst_name=payload.analyst_name,
                    ack_minutes=payload.ack_minutes,
                )
            )
            session.commit()
            return {"accepted": True}
        finally:
            session.close()

    @fastapi_app.post("/api/containment-actions", response_model=ContainmentActionOut)
    def create_containment_action(payload: ContainmentActionIn) -> ContainmentActionOut:
        session = session_factory()
        try:
            current_state = _current_state_of_entity(session, payload.target_entity)
            store = EntityStateStore()
            if current_state != STATE_NORMAL:
                store._set(payload.target_entity, current_state)
            request = ContainmentRequest(
                action_id=payload.action_id,
                incident_id=payload.incident_id,
                action_type=payload.action_type,
                target_entity=payload.target_entity,
                action_minutes=payload.action_minutes,
                approved_by=payload.approved_by,
            )
            result = apply_containment(request, store)
            row = ContainmentActionRow(
                action_id=result.action_id,
                incident_id=payload.incident_id,
                action_type=payload.action_type,
                target_entity=payload.target_entity,
                action_minutes=payload.action_minutes,
                approved_by=result.approved_by,
                executed=result.executed,
                reason=result.reason,
                state_before=result.state_before,
                state_after=result.state_after,
                undone=False,
            )
            session.add(row)
            session.commit()
            return ContainmentActionOut(
                action_id=row.action_id,
                incident_id=row.incident_id,
                action_type=row.action_type,
                target_entity=row.target_entity,
                action_minutes=row.action_minutes,
                approved_by=row.approved_by,
                executed=row.executed,
                reason=row.reason,
                state_before=row.state_before,
                state_after=row.state_after,
                undone=row.undone,
            )
        finally:
            session.close()

    @fastapi_app.post("/api/containment-actions/{action_id}/undo", response_model=UndoOut)
    def undo_containment_action(action_id: str) -> UndoOut:
        session = session_factory()
        try:
            row = session.query(ContainmentActionRow).filter(ContainmentActionRow.action_id == action_id).one_or_none()
            if row is None:
                raise HTTPException(status_code=404, detail="containment action not found")
            if not row.executed:
                raise HTTPException(status_code=400, detail="this action never executed; nothing to undo")
            if row.undone:
                raise HTTPException(status_code=409, detail="this action was already undone")

            store = EntityStateStore()
            store._set(row.target_entity, row.state_before)
            store._set(row.target_entity, row.state_after)
            request = ContainmentRequest(
                action_id=row.action_id,
                incident_id=row.incident_id,
                action_type=row.action_type,
                target_entity=row.target_entity,
                action_minutes=row.action_minutes,
                approved_by=row.approved_by,
            )
            original_result = ContainmentResult(
                action_id=row.action_id,
                executed=row.executed,
                reason=row.reason,
                approved_by=row.approved_by,
                state_before=row.state_before,
                state_after=row.state_after,
            )
            undo_result = undo_containment(request, original_result, store)

            row.undone = True
            session.commit()
            return UndoOut(action_id=row.action_id, undone=undo_result.undone, reason=undo_result.reason)
        finally:
            session.close()
