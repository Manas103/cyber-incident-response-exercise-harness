"""Populates the database from the fixed exercise design (scenarios,
playbook steps, injects) and a demo set of official runs with full
evidence, so a freshly stood-up console has something real to show.
The 40/40 seeded-deviation and clean-run correctness fixtures in
fixtures.py are exercised directly by the test suite and the benchmark
scripts, not written through this path; they are a correctness
measurement, not console demo data."""

from sqlalchemy.orm import Session

from .after_action import EvidenceArtifact
from .fixtures import official_runs
from .injects import INJECTS
from .models import EvidenceArtifactRow, InjectRow, PlaybookStepRow, ResponderActionRow, RunRow, ScenarioRow
from .scenarios import SCENARIOS


def reference_data_is_seeded(session: Session) -> bool:
    return session.query(ScenarioRow).count() > 0


def seed_reference_data(session: Session) -> None:
    if reference_data_is_seeded(session):
        return

    scenario_rows: dict[str, ScenarioRow] = {}
    for scenario in SCENARIOS:
        row = ScenarioRow(
            scenario_id=scenario.scenario_id, name=scenario.name, description=scenario.description
        )
        session.add(row)
        scenario_rows[scenario.scenario_id] = row
    session.flush()

    for scenario in SCENARIOS:
        for step in scenario.steps:
            session.add(
                PlaybookStepRow(
                    step_id=step.step_id,
                    scenario_row_id=scenario_rows[scenario.scenario_id].id,
                    phase=step.phase,
                    order_index=step.order_index,
                    name=step.name,
                )
            )

    for inject in INJECTS:
        session.add(
            InjectRow(
                inject_id=inject.inject_id,
                scenario_row_id=scenario_rows[inject.scenario_id].id,
                order_index=inject.order_index,
                name=inject.name,
                timestamp_minutes=inject.timestamp_minutes,
            )
        )

    session.commit()


def demo_runs_are_seeded(session: Session) -> bool:
    return session.query(RunRow).count() > 0


def seed_demo_runs_with_full_evidence(session: Session) -> None:
    """The 6 official runs (one per scenario, all 24 steps performed
    between them), each step evidenced, so the after-action report the
    console shows on a fresh checkout is the success path (24/24
    exercised). The refusal path is proven separately by
    tests/test_after_action.py, which deliberately withholds evidence
    for one step; that is a correctness property of after_action.py,
    not something the demo data needs to also reproduce."""
    if demo_runs_are_seeded(session):
        return

    inject_rows = {row.inject_id: row for row in session.query(InjectRow).all()}

    for run in official_runs():
        run_row = RunRow(run_id=run.run_id, inject_row_id=inject_rows[run.inject_id].id, kind=run.kind)
        session.add(run_row)
        session.flush()
        for action in run.actions:
            session.add(
                ResponderActionRow(
                    run_row_id=run_row.id,
                    step_id=action.step_id,
                    action_name=action.action_name,
                    timestamp_minutes=action.timestamp_minutes,
                )
            )
            if action.step_id is not None:
                session.add(
                    EvidenceArtifactRow(
                        run_row_id=run_row.id,
                        step_id=action.step_id,
                        artifact_type="log_file",
                        artifact_reference=f"logs/{run.run_id}/{action.step_id}.log",
                    )
                )
    session.commit()


def evidence_rows_to_artifacts(rows: list[EvidenceArtifactRow], run_id_by_row_id: dict[int, str]) -> list[EvidenceArtifact]:
    return [
        EvidenceArtifact(
            run_id=run_id_by_row_id[row.run_row_id],
            step_id=row.step_id,
            artifact_type=row.artifact_type,
            artifact_reference=row.artifact_reference,
        )
        for row in rows
    ]
