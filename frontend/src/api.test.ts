import { afterEach, describe, expect, it, vi } from 'vitest'
import { getAfterActionReport, getRun, listInjects, listRuns, listScenarios } from './api'

describe('api client', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('listScenarios calls the scenarios endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => [] })
    vi.stubGlobal('fetch', fetchMock)
    await listScenarios()
    expect(fetchMock).toHaveBeenCalledWith('/api/scenarios')
  })

  it('listInjects calls the injects endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => [] })
    vi.stubGlobal('fetch', fetchMock)
    await listInjects()
    expect(fetchMock).toHaveBeenCalledWith('/api/injects')
  })

  it('listRuns calls the runs endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => [] })
    vi.stubGlobal('fetch', fetchMock)
    await listRuns()
    expect(fetchMock).toHaveBeenCalledWith('/api/runs')
  })

  it('getRun calls the run detail endpoint with the run id', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) })
    vi.stubGlobal('fetch', fetchMock)
    await getRun('clean.000')
    expect(fetchMock).toHaveBeenCalledWith('/api/runs/clean.000')
  })

  it('getAfterActionReport calls the after-action-report endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) })
    vi.stubGlobal('fetch', fetchMock)
    await getAfterActionReport()
    expect(fetchMock).toHaveBeenCalledWith('/api/after-action-report')
  })

  it('throws on a non-2xx response', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: false, status: 500 })
    vi.stubGlobal('fetch', fetchMock)
    await expect(listRuns()).rejects.toThrow('list runs failed: 500')
  })
})
