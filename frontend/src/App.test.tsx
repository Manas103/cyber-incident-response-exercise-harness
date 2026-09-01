import { render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'

function mockFetchSequence() {
  return vi.fn((url: string) => {
    if (url === '/api/injects') {
      return Promise.resolve({
        ok: true,
        json: async () => [
          {
            inject_id: 'ransomware_corporate_it.inject1',
            scenario_id: 'ransomware_corporate_it',
            scenario_name: 'Ransomware on Corporate IT',
            order_index: 0,
            name: 'Encrypted file extensions observed',
            timestamp_minutes: 0,
          },
        ],
      })
    }
    if (url === '/api/runs') {
      return Promise.resolve({
        ok: true,
        json: async () => [
          {
            run_id: 'official.ransomware_corporate_it',
            inject_id: 'ransomware_corporate_it.inject1',
            inject_name: 'Encrypted file extensions observed',
            scenario_id: 'ransomware_corporate_it',
            scenario_name: 'Ransomware on Corporate IT',
            kind: 'official',
            action_count: 4,
          },
        ],
      })
    }
    if (url === '/api/after-action-report') {
      return Promise.resolve({
        ok: true,
        json: async () => ({ total_steps: 24, exercised_count: 24, not_exercised_count: 0, lines: [] }),
      })
    }
    return Promise.resolve({ ok: false, status: 404 })
  })
}

describe('App', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('loads and renders the timeline, run list and after-action summary', async () => {
    vi.stubGlobal('fetch', mockFetchSequence())
    render(<App />)

    await waitFor(() => expect(screen.getByText('Encrypted file extensions observed')).toBeInTheDocument())
    expect(screen.getByText(/official.ransomware_corporate_it/)).toBeInTheDocument()
    expect(screen.getByText('Exercised 24 of 24 named playbook steps')).toBeInTheDocument()
  })

  it('surfaces a load error', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: false, status: 500 }),
    )
    render(<App />)
    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())
  })
})
