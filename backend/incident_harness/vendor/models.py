"""SQLAlchemy tables for the vendor-feed extension, sharing the main Base/metadata.
VendorAlertRow is the only durable fact; incidents are recomputed from the stored
alerts by correlation.py on every read, the same "derive, do not store" approach
timing.py and detector.py take for the tabletop exercise, because an incident's
membership is a pure function of its alerts and should never drift out of sync
with them. ContainmentActionRow is the one thing that must be stored as-is: who
approved what, and whether it was later undone, is itself the audit record."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..models import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class VendorAlertRow(Base):
    __tablename__ = "vendor_alert"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    feed: Mapped[str] = mapped_column(String(32), nullable=False)
    entities_json: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    data_sensitivity: Mapped[str] = mapped_column(String(32), nullable=False)
    scope: Mapped[str] = mapped_column(String(32), nullable=False)
    actively_exploited: Mapped[bool] = mapped_column(Boolean, nullable=False)
    timestamp_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class AnalystAckRow(Base):
    __tablename__ = "vendor_analyst_ack"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_id: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    analyst_name: Mapped[str] = mapped_column(String(200), nullable=False)
    ack_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class ContainmentActionRow(Base):
    __tablename__ = "containment_action"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    action_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    incident_id: Mapped[str] = mapped_column(String(200), nullable=False)
    action_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_entity: Mapped[str] = mapped_column(String(200), nullable=False)
    action_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    approved_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    executed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reason: Mapped[str] = mapped_column(String(200), nullable=False)
    state_before: Mapped[str | None] = mapped_column(String(32), nullable=True)
    state_after: Mapped[str | None] = mapped_column(String(32), nullable=True)
    undone: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
