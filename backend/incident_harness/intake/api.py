"""Registers the intake extension's routes onto the main FastAPI app: one ingest
endpoint per channel (each normalizes onto IncidentRecordRow and classifies severity),
a listing endpoint, and the notification approval gate. A real production version would
also expose a generic "list by severity" or "list by channel" query; this build keeps the
surface to exactly what the resume bullet claims."""

from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import Session, sessionmaker

from .channels import (
    CustomerReportRaw,
    InternalAlertRaw,
    ResearcherDisclosureRaw,
    normalize_customer_report,
    normalize_internal_alert,
    normalize_researcher_disclosure,
)
from .models import IncidentRecordRow, NotificationRow
from .notification import NotificationRequest, send_notification
from .schemas import (
    CustomerReportIn,
    IncidentRecordOut,
    InternalAlertIn,
    NotificationIn,
    NotificationOut,
    ResearcherDisclosureIn,
)
from .severity import SeverityInputs, classify_severity


def _persist_incident(session: Session, record) -> IncidentRecordRow:
    severity = classify_severity(
        SeverityInputs(
            data_sensitivity=record.data_sensitivity,
            scope=record.scope,
            actively_exploited=record.actively_exploited,
        )
    )
    row = IncidentRecordRow(
        channel=record.channel,
        source_reference=record.source_reference,
        summary=record.summary,
        data_sensitivity=record.data_sensitivity,
        scope=record.scope,
        actively_exploited=record.actively_exploited,
        reported_at_minutes=record.reported_at_minutes,
        severity=severity,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _incident_out(row: IncidentRecordRow) -> IncidentRecordOut:
    return IncidentRecordOut(
        incident_id=row.id,
        channel=row.channel,
        source_reference=row.source_reference,
        summary=row.summary,
        data_sensitivity=row.data_sensitivity,
        scope=row.scope,
        actively_exploited=row.actively_exploited,
        reported_at_minutes=row.reported_at_minutes,
        severity=row.severity,
    )


def register_intake_routes(fastapi_app: FastAPI, session_factory: sessionmaker) -> None:
    @fastapi_app.post("/api/incidents/customer-report", response_model=IncidentRecordOut)
    def ingest_customer_report(payload: CustomerReportIn) -> IncidentRecordOut:
        session = session_factory()
        try:
            record = normalize_customer_report(CustomerReportRaw(**payload.model_dump()))
            row = _persist_incident(session, record)
            return _incident_out(row)
        finally:
            session.close()

    @fastapi_app.post("/api/incidents/internal-alert", response_model=IncidentRecordOut)
    def ingest_internal_alert(payload: InternalAlertIn) -> IncidentRecordOut:
        session = session_factory()
        try:
            record = normalize_internal_alert(InternalAlertRaw(**payload.model_dump()))
            row = _persist_incident(session, record)
            return _incident_out(row)
        finally:
            session.close()

    @fastapi_app.post("/api/incidents/researcher-disclosure", response_model=IncidentRecordOut)
    def ingest_researcher_disclosure(payload: ResearcherDisclosureIn) -> IncidentRecordOut:
        session = session_factory()
        try:
            record = normalize_researcher_disclosure(ResearcherDisclosureRaw(**payload.model_dump()))
            row = _persist_incident(session, record)
            return _incident_out(row)
        finally:
            session.close()

    @fastapi_app.get("/api/incidents", response_model=list[IncidentRecordOut])
    def list_incidents() -> list[IncidentRecordOut]:
        session = session_factory()
        try:
            rows = session.query(IncidentRecordRow).order_by(IncidentRecordRow.id).all()
            return [_incident_out(r) for r in rows]
        finally:
            session.close()

    @fastapi_app.post("/api/incidents/{incident_id}/notifications", response_model=NotificationOut)
    def notify(incident_id: int, payload: NotificationIn) -> NotificationOut:
        session = session_factory()
        try:
            incident = session.get(IncidentRecordRow, incident_id)
            if incident is None:
                raise HTTPException(status_code=404, detail="incident not found")
            result = send_notification(
                NotificationRequest(
                    incident_source_reference=incident.source_reference,
                    message=payload.message,
                    approved_by=payload.approved_by,
                )
            )
            session.add(
                NotificationRow(
                    incident_record_id=incident_id,
                    message=payload.message,
                    approved_by=result.approved_by,
                    sent=result.sent,
                    reason=result.reason,
                )
            )
            session.commit()
            return NotificationOut(
                incident_id=incident_id, sent=result.sent, reason=result.reason, approved_by=result.approved_by
            )
        finally:
            session.close()
