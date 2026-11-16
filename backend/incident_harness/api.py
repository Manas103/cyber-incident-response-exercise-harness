"""FastAPI app: read the fixed scenario/inject timeline, read a run's
actions with its computed timing and deviations, and read the
after-action report, all backed by the same detector.py, timing.py and
after_action.py the benchmark scripts exercise directly."""

from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import Session, sessionmaker

from .after_action import generate_report
from .db import init_schema, make_engine, make_session_factory
from .detector import ActionRecord, detect_deviations
from .fixtures import RunRecordDef
from .intake.api import register_intake_routes
from .models import EvidenceArtifactRow, InjectRow, PlaybookStepRow, ResponderActionRow, RunRow, ScenarioRow
from .schemas import (
    ActionOut,
    AfterActionLineOut,
    AfterActionReportOut,
    DeviationOut,
    InjectOut,
    PlaybookStepOut,
    RunDetailOut,
    RunSummaryOut,
    ScenarioOut,
    TimingOut,
)
from .seed import evidence_rows_to_artifacts, seed_demo_runs_with_full_evidence, seed_reference_data
from .timing import compute_timing
from .injects import InjectDef


def _scenario_out(session: Session, scenario: ScenarioRow) -> ScenarioOut:
    steps = (
        session.query(PlaybookStepRow)
        .filter(PlaybookStepRow.scenario_row_id == scenario.id)
        .order_by(PlaybookStepRow.order_index)
        .all()
    )
    injects = (
        session.query(InjectRow)
        .filter(InjectRow.scenario_row_id == scenario.id)
        .order_by(InjectRow.order_index)
        .all()
    )
    return ScenarioOut(
        scenario_id=scenario.scenario_id,
        name=scenario.name,
        description=scenario.description,
        steps=[
            PlaybookStepOut(step_id=s.step_id, phase=s.phase, order_index=s.order_index, name=s.name)
            for s in steps
        ],
        injects=[
            InjectOut(
                inject_id=i.inject_id,
                scenario_id=scenario.scenario_id,
                scenario_name=scenario.name,
                order_index=i.order_index,
                name=i.name,
                timestamp_minutes=i.timestamp_minutes,
            )
            for i in injects
        ],
    )


def _register_routes(fastapi_app: FastAPI, session_factory: sessionmaker) -> None:
    @fastapi_app.get("/api/scenarios", response_model=list[ScenarioOut])
    def list_scenarios() -> list[ScenarioOut]:
        session = session_factory()
        try:
            scenarios = session.query(ScenarioRow).order_by(ScenarioRow.id).all()
            return [_scenario_out(session, s) for s in scenarios]
        finally:
            session.close()

    @fastapi_app.get("/api/injects", response_model=list[InjectOut])
    def list_injects() -> list[InjectOut]:
        session = session_factory()
        try:
            rows = (
                session.query(InjectRow, ScenarioRow)
                .join(ScenarioRow, InjectRow.scenario_row_id == ScenarioRow.id)
                .order_by(ScenarioRow.id, InjectRow.order_index)
                .all()
            )
            return [
                InjectOut(
                    inject_id=inject.inject_id,
                    scenario_id=scenario.scenario_id,
                    scenario_name=scenario.name,
                    order_index=inject.order_index,
                    name=inject.name,
                    timestamp_minutes=inject.timestamp_minutes,
                )
                for inject, scenario in rows
            ]
        finally:
            session.close()

    @fastapi_app.get("/api/runs", response_model=list[RunSummaryOut])
    def list_runs() -> list[RunSummaryOut]:
        session = session_factory()
        try:
            rows = (
                session.query(RunRow, InjectRow, ScenarioRow)
                .join(InjectRow, RunRow.inject_row_id == InjectRow.id)
                .join(ScenarioRow, InjectRow.scenario_row_id == ScenarioRow.id)
                .order_by(RunRow.id)
                .all()
            )
            out = []
            for run, inject, scenario in rows:
                action_count = (
                    session.query(ResponderActionRow)
                    .filter(ResponderActionRow.run_row_id == run.id)
                    .count()
                )
                out.append(
                    RunSummaryOut(
                        run_id=run.run_id,
                        inject_id=inject.inject_id,
                        inject_name=inject.name,
                        scenario_id=scenario.scenario_id,
                        scenario_name=scenario.name,
                        kind=run.kind,
                        action_count=action_count,
                    )
                )
            return out
        finally:
            session.close()

    @fastapi_app.get("/api/runs/{run_id}", response_model=RunDetailOut)
    def get_run(run_id: str) -> RunDetailOut:
        session = session_factory()
        try:
            run = session.query(RunRow).filter(RunRow.run_id == run_id).one_or_none()
            if run is None:
                raise HTTPException(status_code=404, detail="run not found")
            inject_row = session.get(InjectRow, run.inject_row_id)
            scenario_row = session.get(ScenarioRow, inject_row.scenario_row_id)
            action_rows = (
                session.query(ResponderActionRow)
                .filter(ResponderActionRow.run_row_id == run.id)
                .order_by(ResponderActionRow.timestamp_minutes)
                .all()
            )
            actions = [
                ActionRecord(
                    action_name=a.action_name, timestamp_minutes=a.timestamp_minutes, step_id=a.step_id
                )
                for a in action_rows
            ]
            inject_def = InjectDef(
                inject_id=inject_row.inject_id,
                scenario_id=scenario_row.scenario_id,
                order_index=inject_row.order_index,
                name=inject_row.name,
                timestamp_minutes=inject_row.timestamp_minutes,
            )
            timing = compute_timing(inject_def, actions)
            deviations = detect_deviations(
                run_id=run.run_id,
                inject_id=inject_row.inject_id,
                scenario_id=scenario_row.scenario_id,
                actions=actions,
            )
            return RunDetailOut(
                run_id=run.run_id,
                inject_id=inject_row.inject_id,
                scenario_id=scenario_row.scenario_id,
                kind=run.kind,
                actions=[
                    ActionOut(step_id=a.step_id, action_name=a.action_name, timestamp_minutes=a.timestamp_minutes)
                    for a in action_rows
                ],
                timing=TimingOut(
                    time_to_detect_minutes=timing.time_to_detect_minutes,
                    time_to_contain_minutes=timing.time_to_contain_minutes,
                ),
                deviations=[
                    DeviationOut(
                        step_id=d.step_id, step_name=d.step_name, deviation_type=d.deviation_type, detail=d.detail
                    )
                    for d in deviations
                ],
            )
        finally:
            session.close()

    @fastapi_app.get("/api/after-action-report", response_model=AfterActionReportOut)
    def after_action_report() -> AfterActionReportOut:
        session = session_factory()
        try:
            official_run_rows = session.query(RunRow).filter(RunRow.kind == "official").all()
            run_defs = []
            for run in official_run_rows:
                action_rows = (
                    session.query(ResponderActionRow).filter(ResponderActionRow.run_row_id == run.id).all()
                )
                inject_row = session.get(InjectRow, run.inject_row_id)
                scenario_row = session.get(ScenarioRow, inject_row.scenario_row_id)
                run_defs.append(
                    RunRecordDef(
                        run_id=run.run_id,
                        inject_id=inject_row.inject_id,
                        scenario_id=scenario_row.scenario_id,
                        kind=run.kind,
                        actions=tuple(
                            ActionRecord(
                                action_name=a.action_name, timestamp_minutes=a.timestamp_minutes, step_id=a.step_id
                            )
                            for a in action_rows
                        ),
                    )
                )
            run_row_ids = [r.id for r in official_run_rows]
            evidence_rows = (
                session.query(EvidenceArtifactRow)
                .filter(EvidenceArtifactRow.run_row_id.in_(run_row_ids))
                .all()
                if run_row_ids
                else []
            )
            run_id_by_row_id = {r.id: r.run_id for r in official_run_rows}
            evidence = evidence_rows_to_artifacts(evidence_rows, run_id_by_row_id)
            report = generate_report(run_defs, evidence)
            return AfterActionReportOut(
                total_steps=report.total_steps,
                exercised_count=report.exercised_count,
                not_exercised_count=report.not_exercised_count,
                lines=[
                    AfterActionLineOut(
                        step_id=line.step_id,
                        step_name=line.step_name,
                        scenario_id=line.scenario_id,
                        phase=line.phase,
                        status=line.status,
                        reason=line.reason,
                        evidence_reference=line.evidence_reference,
                    )
                    for line in report.lines
                ],
            )
        finally:
            session.close()


def create_app(database_url: str | None = None, seed: bool = True) -> FastAPI:
    """Factory so tests can point the app at an isolated database instead
    of sharing the module-level default; `app` below is the default
    instance uvicorn would serve. `seed=False` lets tests build an
    intentionally empty database."""
    fastapi_app = FastAPI(title="Cyber Incident Response Exercise Harness")
    engine = make_engine(database_url)
    session_factory = make_session_factory(engine)
    init_schema(engine)
    if seed:
        session = session_factory()
        try:
            seed_reference_data(session)
            seed_demo_runs_with_full_evidence(session)
        finally:
            session.close()
    fastapi_app.state.engine = engine
    _register_routes(fastapi_app, session_factory)
    register_intake_routes(fastapi_app, session_factory)
    return fastapi_app


app = create_app()
