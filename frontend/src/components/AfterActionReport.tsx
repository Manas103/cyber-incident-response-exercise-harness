import type { AfterActionReportView } from '../types'

interface Props {
  report: AfterActionReportView | null
}

export function AfterActionReport({ report }: Props) {
  if (report === null) {
    return <p>Loading after-action report...</p>
  }

  return (
    <div data-testid="after-action-report">
      <p>
        Exercised {report.exercised_count} of {report.total_steps} named playbook steps
      </p>
      <table>
        <thead>
          <tr>
            <th>Step</th>
            <th>Phase</th>
            <th>Status</th>
            <th>Reason</th>
            <th>Evidence</th>
          </tr>
        </thead>
        <tbody>
          {report.lines.map((line) => (
            <tr key={line.step_id}>
              <td>{line.step_name}</td>
              <td>{line.phase}</td>
              <td className={`status-${line.status}`}>{line.status}</td>
              <td>{line.reason}</td>
              <td>{line.evidence_reference ?? 'none'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
