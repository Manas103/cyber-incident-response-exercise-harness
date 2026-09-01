import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { AfterActionReport } from './AfterActionReport'
import type { AfterActionReportView } from '../types'

describe('AfterActionReport', () => {
  it('shows a loading message when the report has not arrived yet', () => {
    render(<AfterActionReport report={null} />)
    expect(screen.getByText('Loading after-action report...')).toBeInTheDocument()
  })

  it('shows exercised and not-exercised steps with their reasons', () => {
    const report: AfterActionReportView = {
      total_steps: 24,
      exercised_count: 23,
      not_exercised_count: 1,
      lines: [
        {
          step_id: 'ransomware_corporate_it.detect',
          step_name: 'Identify mass file-encryption activity via EDR alert triage',
          scenario_id: 'ransomware_corporate_it',
          phase: 'detect',
          status: 'exercised',
          reason: 'performed and evidenced',
          evidence_reference: 'log_file:logs/official.ransomware_corporate_it/detect.log',
        },
        {
          step_id: 'ransomware_corporate_it.contain',
          step_name: 'Isolate affected hosts from the corporate network segment',
          scenario_id: 'ransomware_corporate_it',
          phase: 'contain',
          status: 'not_exercised',
          reason: 'step was performed but has no linked evidence artifact',
          evidence_reference: null,
        },
      ],
    }
    render(<AfterActionReport report={report} />)
    expect(screen.getByText('Exercised 23 of 24 named playbook steps')).toBeInTheDocument()
    expect(screen.getByText('step was performed but has no linked evidence artifact')).toBeInTheDocument()
    expect(screen.getByText('none')).toBeInTheDocument()
  })
})
