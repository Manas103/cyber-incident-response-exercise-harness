"""After-action report generator, one line per named playbook step (24
across the 6 scenarios, 4 per scenario). A step is marked "exercised"
only when both are true: the exercise record shows a matching
responder action for it, and an evidence artifact record is linked to
that (run, step) pair. If either is missing, the report marks the step
"not_exercised" and states which of the two conditions failed; it never
guesses "probably exercised" from partial information."""

from dataclasses import dataclass

from .fixtures import RunRecordDef
from .scenarios import all_steps


@dataclass(frozen=True)
class EvidenceArtifact:
    run_id: str
    step_id: str
    artifact_type: str  # e.g. "log_file", "ticket_id", "screenshot"
    artifact_reference: str


@dataclass(frozen=True)
class StepReportLine:
    step_id: str
    step_name: str
    scenario_id: str
    phase: str
    status: str  # "exercised" or "not_exercised"
    reason: str
    evidence_reference: str | None


@dataclass(frozen=True)
class AfterActionReport:
    lines: tuple[StepReportLine, ...]

    @property
    def total_steps(self) -> int:
        return len(self.lines)

    @property
    def exercised_count(self) -> int:
        return sum(1 for line in self.lines if line.status == "exercised")

    @property
    def not_exercised_count(self) -> int:
        return sum(1 for line in self.lines if line.status == "not_exercised")


def _performed_step_ids(run: RunRecordDef) -> set[str]:
    return {a.step_id for a in run.actions if a.step_id is not None}


def generate_report(
    runs: list[RunRecordDef], evidence: list[EvidenceArtifact]
) -> AfterActionReport:
    """`runs` is the set of official exercise runs (one per scenario, by
    convention, though the function does not require that shape).
    `evidence` is every evidence artifact record attached during the
    exercise. A step can be performed in more than one run; it counts
    as performed if any run's action log shows it, and as evidenced if
    any evidence record names it for a run that performed it."""

    performed_by_step: dict[str, str] = {}  # step_id -> a run_id that performed it
    for run in runs:
        for step_id in _performed_step_ids(run):
            performed_by_step.setdefault(step_id, run.run_id)

    evidence_by_step: dict[str, EvidenceArtifact] = {}
    for record in evidence:
        if record.run_id == performed_by_step.get(record.step_id):
            evidence_by_step[record.step_id] = record

    lines: list[StepReportLine] = []
    for step in all_steps():
        performing_run = performed_by_step.get(step.step_id)
        if performing_run is None:
            lines.append(
                StepReportLine(
                    step_id=step.step_id,
                    step_name=step.name,
                    scenario_id=step.scenario_id,
                    phase=step.phase,
                    status="not_exercised",
                    reason="step was not performed in any official exercise run",
                    evidence_reference=None,
                )
            )
            continue

        artifact = evidence_by_step.get(step.step_id)
        if artifact is None:
            lines.append(
                StepReportLine(
                    step_id=step.step_id,
                    step_name=step.name,
                    scenario_id=step.scenario_id,
                    phase=step.phase,
                    status="not_exercised",
                    reason="step was performed but has no linked evidence artifact",
                    evidence_reference=None,
                )
            )
            continue

        lines.append(
            StepReportLine(
                step_id=step.step_id,
                step_name=step.name,
                scenario_id=step.scenario_id,
                phase=step.phase,
                status="exercised",
                reason="performed and evidenced",
                evidence_reference=f"{artifact.artifact_type}:{artifact.artifact_reference}",
            )
        )

    return AfterActionReport(lines=tuple(lines))
