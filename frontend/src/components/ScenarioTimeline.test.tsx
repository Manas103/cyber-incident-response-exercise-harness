import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ScenarioTimeline } from './ScenarioTimeline'
import type { InjectView } from '../types'

const injects: InjectView[] = [
  {
    inject_id: 'ransomware_corporate_it.inject1',
    scenario_id: 'ransomware_corporate_it',
    scenario_name: 'Ransomware on Corporate IT',
    order_index: 0,
    name: 'Encrypted file extensions observed',
    timestamp_minutes: 0,
  },
  {
    inject_id: 'ransomware_corporate_it.inject2',
    scenario_id: 'ransomware_corporate_it',
    scenario_name: 'Ransomware on Corporate IT',
    order_index: 1,
    name: 'Ransom note dropped',
    timestamp_minutes: 15,
  },
]

describe('ScenarioTimeline', () => {
  it('shows a message when there are no injects', () => {
    render(<ScenarioTimeline injects={[]} />)
    expect(screen.getByText('No injects loaded.')).toBeInTheDocument()
  })

  it('groups injects by scenario and renders each inject name and timestamp', () => {
    render(<ScenarioTimeline injects={injects} />)
    expect(screen.getByText('Ransomware on Corporate IT')).toBeInTheDocument()
    expect(screen.getByText('Encrypted file extensions observed')).toBeInTheDocument()
    expect(screen.getByText('Ransom note dropped')).toBeInTheDocument()
    expect(screen.getByText('15')).toBeInTheDocument()
  })
})
