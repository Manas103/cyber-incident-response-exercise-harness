import { useEffect, useState } from 'react'
import { getAfterActionReport, getRun, listInjects, listRuns } from './api'
import { AfterActionReport } from './components/AfterActionReport'
import { DeviationsPanel } from './components/DeviationsPanel'
import { ScenarioTimeline } from './components/ScenarioTimeline'
import type { AfterActionReportView, DeviationView, InjectView, RunSummaryView } from './types'

function App() {
  const [injects, setInjects] = useState<InjectView[]>([])
  const [runs, setRuns] = useState<RunSummaryView[]>([])
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)
  const [deviations, setDeviations] = useState<DeviationView[]>([])
  const [report, setReport] = useState<AfterActionReportView | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const [loadedInjects, loadedRuns, loadedReport] = await Promise.all([
          listInjects(),
          listRuns(),
          getAfterActionReport(),
        ])
        setInjects(loadedInjects)
        setRuns(loadedRuns)
        setReport(loadedReport)
        setLoadError(null)
      } catch (err) {
        setLoadError(err instanceof Error ? err.message : 'failed to load the exercise harness')
      }
    }
    load()
  }, [])

  const handleSelectRun = async (runId: string) => {
    setSelectedRunId(runId)
    const detail = await getRun(runId)
    setDeviations(detail.deviations)
  }

  return (
    <div className="harness-app">
      <h1>Cyber Incident Response Exercise Harness</h1>
      <p className="tagline">
        6 scenarios, 30 injects, one written playbook per scenario. Every run's actions are checked
        against its playbook and every deviation is named by step, inject and kind.
      </p>
      {loadError && <p role="alert">{loadError}</p>}

      <h2>Scenario timeline</h2>
      <ScenarioTimeline injects={injects} />

      <h2>Runs</h2>
      <ul>
        {runs.map((run) => (
          <li key={run.run_id}>
            <button onClick={() => handleSelectRun(run.run_id)}>
              {run.run_id} ({run.scenario_name} / {run.inject_name})
            </button>
          </li>
        ))}
      </ul>

      <h2>Deviations</h2>
      <DeviationsPanel runId={selectedRunId} deviations={deviations} />

      <h2>After-action report</h2>
      <AfterActionReport report={report} />
    </div>
  )
}

export default App
