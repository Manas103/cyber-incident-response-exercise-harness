"""Pydantic response shapes, typed 1:1 against what src/types.ts expects
on the console side."""

from pydantic import BaseModel


class PlaybookStepOut(BaseModel):
    step_id: str
    phase: str
    order_index: int
    name: str


class InjectOut(BaseModel):
    inject_id: str
    scenario_id: str
    scenario_name: str
    order_index: int
    name: str
    timestamp_minutes: int


class ScenarioOut(BaseModel):
    scenario_id: str
    name: str
    description: str
    steps: list[PlaybookStepOut]
    injects: list[InjectOut]


class ActionOut(BaseModel):
    step_id: str | None
    action_name: str
    timestamp_minutes: int


class DeviationOut(BaseModel):
    step_id: str
    step_name: str
    deviation_type: str
    detail: str


class TimingOut(BaseModel):
    time_to_detect_minutes: int | None
    time_to_contain_minutes: int | None


class RunSummaryOut(BaseModel):
    run_id: str
    inject_id: str
    inject_name: str
    scenario_id: str
    scenario_name: str
    kind: str
    action_count: int


class RunDetailOut(BaseModel):
    run_id: str
    inject_id: str
    scenario_id: str
    kind: str
    actions: list[ActionOut]
    timing: TimingOut
    deviations: list[DeviationOut]


class AfterActionLineOut(BaseModel):
    step_id: str
    step_name: str
    scenario_id: str
    phase: str
    status: str
    reason: str
    evidence_reference: str | None


class AfterActionReportOut(BaseModel):
    total_steps: int
    exercised_count: int
    not_exercised_count: int
    lines: list[AfterActionLineOut]
