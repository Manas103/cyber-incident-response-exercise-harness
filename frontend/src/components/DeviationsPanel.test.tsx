import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { DeviationsPanel } from './DeviationsPanel'
import type { DeviationView } from '../types'

describe('DeviationsPanel', () => {
  it('prompts for a run when none is selected', () => {
    render(<DeviationsPanel runId={null} deviations={[]} />)
    expect(screen.getByText('Select a run to see its deviations.')).toBeInTheDocument()
  })

  it('shows no-deviations message for a clean run', () => {
    render(<DeviationsPanel runId="clean.000" deviations={[]} />)
    expect(screen.getByTestId('no-deviations')).toHaveTextContent('clean.000')
  })

  it('names the step, run and deviation type for a flagged run', () => {
    const deviations: DeviationView[] = [
      {
        step_id: 'ransomware_corporate_it.contain',
        step_name: 'Isolate affected hosts from the corporate network segment',
        deviation_type: 'missing_step',
        detail: 'expected step has no matching responder action',
      },
    ]
    render(<DeviationsPanel runId="seeded.000" deviations={deviations} />)
    expect(screen.getByTestId('deviations-table')).toBeInTheDocument()
    expect(screen.getByText('Isolate affected hosts from the corporate network segment')).toBeInTheDocument()
    expect(screen.getByText('missing_step')).toBeInTheDocument()
    expect(screen.getAllByText('seeded.000').length).toBeGreaterThan(0)
  })
})
