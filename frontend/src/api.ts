import type { AfterActionReportView, InjectView, RunDetailView, RunSummaryView, ScenarioView } from './types'

const BASE = '/api'

export async function listScenarios(): Promise<ScenarioView[]> {
  const response = await fetch(`${BASE}/scenarios`)
  if (!response.ok) {
    throw new Error(`list scenarios failed: ${response.status}`)
  }
  return response.json()
}

export async function listInjects(): Promise<InjectView[]> {
  const response = await fetch(`${BASE}/injects`)
  if (!response.ok) {
    throw new Error(`list injects failed: ${response.status}`)
  }
  return response.json()
}

export async function listRuns(): Promise<RunSummaryView[]> {
  const response = await fetch(`${BASE}/runs`)
  if (!response.ok) {
    throw new Error(`list runs failed: ${response.status}`)
  }
  return response.json()
}

export async function getRun(runId: string): Promise<RunDetailView> {
  const response = await fetch(`${BASE}/runs/${runId}`)
  if (!response.ok) {
    throw new Error(`get run failed: ${response.status}`)
  }
  return response.json()
}

export async function getAfterActionReport(): Promise<AfterActionReportView> {
  const response = await fetch(`${BASE}/after-action-report`)
  if (!response.ok) {
    throw new Error(`get after-action report failed: ${response.status}`)
  }
  return response.json()
}
