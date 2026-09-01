"""SQLAlchemy tables backing the console: scenarios, their playbook
steps and injects (seeded once from the fixed definitions in
scenarios.py / injects.py), and the runs, responder actions, and
evidence artifacts recorded against them. Deviations and timing are
never stored; they are recomputed on every read from detector.py and
timing.py against the current action rows, exactly as
ai-governance-audit-readiness-register never persists a verdict."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ScenarioRow(Base):
    __tablename__ = "scenario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scenario_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    steps: Mapped[list["PlaybookStepRow"]] = relationship(back_populates="scenario")
    injects: Mapped[list["InjectRow"]] = relationship(back_populates="scenario")


class PlaybookStepRow(Base):
    __tablename__ = "playbook_step"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    step_id: Mapped[str] = mapped_column(String(96), unique=True, nullable=False)
    scenario_row_id: Mapped[int] = mapped_column(ForeignKey("scenario.id"), nullable=False)
    phase: Mapped[str] = mapped_column(String(32), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)

    scenario: Mapped["ScenarioRow"] = relationship(back_populates="steps")


class InjectRow(Base):
    __tablename__ = "inject"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    inject_id: Mapped[str] = mapped_column(String(96), unique=True, nullable=False)
    scenario_row_id: Mapped[int] = mapped_column(ForeignKey("scenario.id"), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(400), nullable=False)
    timestamp_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    scenario: Mapped["ScenarioRow"] = relationship(back_populates="injects")
    runs: Mapped[list["RunRow"]] = relationship(back_populates="inject")


class RunRow(Base):
    __tablename__ = "run"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[str] = mapped_column(String(96), unique=True, nullable=False)
    inject_row_id: Mapped[int] = mapped_column(ForeignKey("inject.id"), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    inject: Mapped["InjectRow"] = relationship(back_populates="runs")
    actions: Mapped[list["ResponderActionRow"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    evidence: Mapped[list["EvidenceArtifactRow"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class ResponderActionRow(Base):
    __tablename__ = "responder_action"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_row_id: Mapped[int] = mapped_column(ForeignKey("run.id"), nullable=False)
    step_id: Mapped[str | None] = mapped_column(String(96), nullable=True)
    action_name: Mapped[str] = mapped_column(String(400), nullable=False)
    timestamp_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    run: Mapped["RunRow"] = relationship(back_populates="actions")


class EvidenceArtifactRow(Base):
    __tablename__ = "evidence_artifact"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_row_id: Mapped[int] = mapped_column(ForeignKey("run.id"), nullable=False)
    step_id: Mapped[str] = mapped_column(String(96), nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(64), nullable=False)
    artifact_reference: Mapped[str] = mapped_column(String(400), nullable=False)
    attached_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    run: Mapped["RunRow"] = relationship(back_populates="evidence")
