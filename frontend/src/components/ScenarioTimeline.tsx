import type { InjectView } from '../types'

interface Props {
  injects: InjectView[]
}

export function ScenarioTimeline({ injects }: Props) {
  if (injects.length === 0) {
    return <p>No injects loaded.</p>
  }

  const byScenario = new Map<string, InjectView[]>()
  for (const inject of injects) {
    const list = byScenario.get(inject.scenario_name) ?? []
    list.push(inject)
    byScenario.set(inject.scenario_name, list)
  }

  return (
    <div data-testid="scenario-timeline">
      {[...byScenario.entries()].map(([scenarioName, scenarioInjects]) => (
        <div key={scenarioName}>
          <h3>{scenarioName}</h3>
          <table>
            <thead>
              <tr>
                <th>t (min)</th>
                <th>Inject</th>
              </tr>
            </thead>
            <tbody>
              {scenarioInjects
                .slice()
                .sort((a, b) => a.order_index - b.order_index)
                .map((inject) => (
                  <tr key={inject.inject_id}>
                    <td>{inject.timestamp_minutes}</td>
                    <td>{inject.name}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  )
}
