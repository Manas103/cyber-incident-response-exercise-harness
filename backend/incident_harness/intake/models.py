"""SQLAlchemy tables for the intake extension, sharing the main Base/metadata so
scripts/init_db.py stands up these tables alongside the exercise-harness ones with one
call. A notification's approval state is stored, not recomputed, because unlike a
deviation or timing verdict (recomputed from immutable action rows), who approved a real
customer notification and when is itself the audit record."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..models import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class IncidentRecordRow(Base):
    __tablename__ = "incident_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    source_reference: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    data_sensitivity: Mapped[str] = mapped_column(String(32), nullable=False)
    scope: Mapped[str] = mapped_column(String(32), nullable=False)
    actively_exploited: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reported_at_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    severity: Mapped[str] = mapped_column(String(8), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class NotificationRow(Base):
    __tablename__ = "notification"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_record_id: Mapped[int] = mapped_column(Integer, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    approved_by: Mapped[str | None] = mapped_column(String(200), nullable=True)
    sent: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reason: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
