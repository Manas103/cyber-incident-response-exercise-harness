import type { DeviationView } from '../types'

interface Props {
  runId: string | null
  deviations: DeviationView[]
}

export function DeviationsPanel({ runId, deviations }: Props) {
  if (runId === null) {
    return <p>Select a run to see its deviations.</p>
  }

  if (deviations.length === 0) {
    return <p data-testid="no-deviations">No deviations flagged for {runId}.</p>
  }

  return (
    <table data-testid="deviations-table">
      <thead>
        <tr>
          <th>Run</th>
          <th>Step</th>
          <th>Type</th>
          <th>Detail</th>
        </tr>
      </thead>
      <tbody>
        {deviations.map((deviation) => (
          <tr key={`${runId}-${deviation.step_id}-${deviation.deviation_type}`}>
            <td>{runId}</td>
            <td>{deviation.step_name}</td>
            <td className={`deviation-${deviation.deviation_type}`}>{deviation.deviation_type}</td>
            <td>{deviation.detail}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
