// Typed 1:1 against incident_harness/schemas.py's response shapes.

export interface PlaybookStepView {
  step_id: string
  phase: string
  order_index: number
  name: string
}

export interface InjectView {
  inject_id: string
  scenario_id: string
  scenario_name: string
  order_index: number
  name: string
  timestamp_minutes: number
}

export interface ScenarioView {
  scenario_id: string
  name: string
  description: string
  steps: PlaybookStepView[]
  injects: InjectView[]
}

export interface ActionView {
  step_id: string | null
  action_name: string
  timestamp_minutes: number
}

export interface DeviationView {
  step_id: string
  step_name: string
  deviation_type: string
  detail: string
}

export interface TimingView {
  time_to_detect_minutes: number | null
  time_to_contain_minutes: number | null
}

export interface RunSummaryView {
  run_id: string
  inject_id: string
  inject_name: string
  scenario_id: string
  scenario_name: string
  kind: string
  action_count: number
}

export interface RunDetailView {
  run_id: string
  inject_id: string
  scenario_id: string
  kind: string
  actions: ActionView[]
  timing: TimingView
  deviations: DeviationView[]
}

export interface AfterActionLineView {
  step_id: string
  step_name: string
  scenario_id: string
  phase: string
  status: string
  reason: string
  evidence_reference: string | null
}

export interface AfterActionReportView {
  total_steps: number
  exercised_count: number
  not_exercised_count: number
  lines: AfterActionLineView[]
}
