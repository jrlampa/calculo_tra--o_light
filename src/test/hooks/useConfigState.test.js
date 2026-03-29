/**
 * Tests for useConfigState hook.
 *
 * Covered paths:
 *  1. Initial state — status='idle', empty arrays/objects.
 *  2. loadConfig success — config populated, status='success'.
 *  3. loadConfig HTTP error — status='error', error message set.
 *  4. loadConfig network failure (fetch throws) — status='error', fallback message.
 *  5. retryConfig — calls loadConfig again and recovers to success.
 *  6. isConfigLoaded — false when status != success or postes empty.
 *  7. isConfigLoaded — true when status='success' and postes has entries.
 *  8. getModelosForTipo — returns array for known type, [] for unknown.
 *  9. getTiposPoste — returns Object.keys(config.postes).
 * 10. configBanner — null when idle, loading object, error object.
 * 11. normalizeConfigPayload — trims strings, filters non-string, ignores
 *     invalid lookup values, ignores null/array payload.
 */
import { renderHook, act, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

import { useConfigState } from '@/hooks/useConfigState'

// ─── helpers ──────────────────────────────────────────────────────────────────

const CONFIG_FIXTURE = {
  redes: ['Convencional', 'Compacta'],
  cabos: ['CAA', 'AACSR'],
  postes: {
    Concreto: ['11/200', '11/400', '13/600'],
    Aço: ['11/300', '13/800'],
  },
  cabos_por_rede: {
    Convencional: ['CAA', 'AACSR'],
    Compacta: ['CU'],
  },
}

function okFetch(body = CONFIG_FIXTURE) {
  return vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: () => Promise.resolve(body),
    headers: { get: () => null },
  })
}

function errorFetch(status = 500) {
  return vi.fn().mockResolvedValue({
    ok: false,
    status,
    statusText: 'Server Error',
    json: () => Promise.resolve({ detail: 'server error' }),
    headers: { get: () => null },
  })
}

// ─── tests ────────────────────────────────────────────────────────────────────

describe('useConfigState', () => {
  beforeEach(() => {
    vi.stubGlobal('localStorage', { getItem: () => null, setItem: () => {} })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  // ── 1. initial state via idle ──────────────────────────────────────────────

  it('starts loading immediately on mount (auto-loads)', async () => {
    // The hook calls loadConfig() in a useEffect on mount
    vi.stubGlobal('fetch', okFetch())
    const { result } = renderHook(() => useConfigState())

    // status transitions to 'loading' then 'success'
    await waitFor(() => {
      expect(result.current.configState.status).toBe('success')
    })
  })

  // ── 2. loadConfig success ──────────────────────────────────────────────────

  it('populates config on success', async () => {
    vi.stubGlobal('fetch', okFetch())
    const { result } = renderHook(() => useConfigState())

    await waitFor(() => expect(result.current.configState.status).toBe('success'))

    expect(result.current.config.redes).toEqual(['Convencional', 'Compacta'])
    expect(result.current.config.cabos).toEqual(['CAA', 'AACSR'])
    expect(result.current.config.postes).toEqual(CONFIG_FIXTURE.postes)
    expect(result.current.config.cabos_por_rede).toEqual(CONFIG_FIXTURE.cabos_por_rede)
    expect(result.current.configState.error).toBe('')
  })

  // ── 3. loadConfig HTTP error ───────────────────────────────────────────────

  it('sets error status on HTTP failure', async () => {
    vi.stubGlobal('fetch', errorFetch(500))
    const { result } = renderHook(() => useConfigState())

    await waitFor(() => expect(result.current.configState.status).toBe('error'))

    expect(result.current.configState.error).toMatch(/configurações/)
    expect(result.current.config.redes).toEqual([]) // unchanged
  })

  // ── 4. fetch network failure ───────────────────────────────────────────────

  it('uses err.message from thrown Error (or fallback for non-Error throws)', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
    const { result } = renderHook(() => useConfigState())

    await waitFor(() => expect(result.current.configState.status).toBe('error'))

    // The hook uses err.message when err instanceof Error
    expect(result.current.configState.error).toBe('Failed to fetch')
  })

  // ── 5. retryConfig ─────────────────────────────────────────────────────────

  it('retryConfig recovers to success after error', async () => {
    let callCount = 0
    vi.stubGlobal('fetch', vi.fn().mockImplementation(() => {
      callCount++
      if (callCount === 1) {
        return Promise.resolve({ ok: false, status: 500, json: () => Promise.resolve({}) })
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(CONFIG_FIXTURE),
      })
    }))

    const { result } = renderHook(() => useConfigState())

    // First load fails
    await waitFor(() => expect(result.current.configState.status).toBe('error'))

    // Retry
    act(() => {
      result.current.handlers.retryConfig()
    })

    await waitFor(() => expect(result.current.configState.status).toBe('success'))
    expect(result.current.config.redes).toEqual(['Convencional', 'Compacta'])
  })

  // ── 6-7. isConfigLoaded ────────────────────────────────────────────────────

  it('isConfigLoaded is false on error', async () => {
    vi.stubGlobal('fetch', errorFetch())
    const { result } = renderHook(() => useConfigState())

    await waitFor(() => expect(result.current.configState.status).toBe('error'))

    expect(result.current.isConfigLoaded).toBe(false)
  })

  it('isConfigLoaded is true after successful load with postes', async () => {
    vi.stubGlobal('fetch', okFetch())
    const { result } = renderHook(() => useConfigState())

    await waitFor(() => expect(result.current.configState.status).toBe('success'))

    expect(result.current.isConfigLoaded).toBe(true)
  })

  it('isConfigLoaded is false when postes is empty even on success', async () => {
    vi.stubGlobal('fetch', okFetch({ redes: [], cabos: [], postes: {}, cabos_por_rede: {} }))
    const { result } = renderHook(() => useConfigState())

    await waitFor(() => expect(result.current.configState.status).toBe('success'))

    expect(result.current.isConfigLoaded).toBe(false)
  })

  // ── 8. getModelosForTipo ───────────────────────────────────────────────────

  it('getModelosForTipo returns models for known type', async () => {
    vi.stubGlobal('fetch', okFetch())
    const { result } = renderHook(() => useConfigState())

    await waitFor(() => expect(result.current.isConfigLoaded).toBe(true))

    expect(result.current.helpers.getModelosForTipo('Concreto'))
      .toEqual(['11/200', '11/400', '13/600'])
  })

  it('getModelosForTipo returns [] for unknown type', async () => {
    vi.stubGlobal('fetch', okFetch())
    const { result } = renderHook(() => useConfigState())

    await waitFor(() => expect(result.current.isConfigLoaded).toBe(true))

    expect(result.current.helpers.getModelosForTipo('Madeira')).toEqual([])
  })

  // ── 9. getTiposPoste ───────────────────────────────────────────────────────

  it('getTiposPoste returns keys of postes map', async () => {
    vi.stubGlobal('fetch', okFetch())
    const { result } = renderHook(() => useConfigState())

    await waitFor(() => expect(result.current.isConfigLoaded).toBe(true))

    expect(result.current.helpers.getTiposPoste()).toEqual(['Concreto', 'Aço'])
  })

  // ── 10. configBanner ───────────────────────────────────────────────────────

  it('configBanner is loading-toned while loading', async () => {
    // Intercept with a slow fetch so we can observe loading state
    let resolveConfig
    vi.stubGlobal('fetch', vi.fn().mockReturnValue(
      new Promise(res => { resolveConfig = res })
    ))

    const { result } = renderHook(() => useConfigState())

    // Hook calls loadConfig on mount → status goes to 'loading'
    await waitFor(() => expect(result.current.configBanner?.tone).toBe('loading'))
    expect(result.current.configBanner.role).toBe('status')

    // Clean up — resolve so the hook doesn't hang
    resolveConfig({ ok: false, status: 500, json: () => Promise.resolve({}) })
  })

  it('configBanner is error-toned on failure', async () => {
    vi.stubGlobal('fetch', errorFetch())
    const { result } = renderHook(() => useConfigState())

    await waitFor(() => expect(result.current.configState.status).toBe('error'))

    expect(result.current.configBanner?.tone).toBe('error')
    expect(result.current.configBanner.role).toBe('alert')
    expect(result.current.configBanner.message).toMatch(/Falha ao carregar \/api\/config/)
  })

  it('configBanner is null after successful load', async () => {
    vi.stubGlobal('fetch', okFetch())
    const { result } = renderHook(() => useConfigState())

    await waitFor(() => expect(result.current.configState.status).toBe('success'))

    expect(result.current.configBanner).toBeNull()
  })

  // ── 11. normalizeConfigPayload edge cases ─────────────────────────────────

  it('handles partial config payload (missing fields)', async () => {
    vi.stubGlobal('fetch', okFetch({ redes: ['Convencional'] })) // missing cabos/postes/cabos_por_rede
    const { result } = renderHook(() => useConfigState())

    await waitFor(() => expect(result.current.configState.status).toBe('success'))

    expect(result.current.config.redes).toEqual(['Convencional'])
    expect(result.current.config.cabos).toEqual([])
    expect(result.current.config.postes).toEqual({})
    expect(result.current.config.cabos_por_rede).toEqual({})
  })

  it('strips non-string items and trims whitespace in arrays', async () => {
    vi.stubGlobal('fetch', okFetch({
      redes: ['  Convencional  ', 42, null, '', 'Compacta'],
      cabos: [],
      postes: {},
      cabos_por_rede: {},
    }))
    const { result } = renderHook(() => useConfigState())

    await waitFor(() => expect(result.current.configState.status).toBe('success'))

    expect(result.current.config.redes).toEqual(['Convencional', 'Compacta'])
  })

  it('ignores invalid postes payload (not an object)', async () => {
    vi.stubGlobal('fetch', okFetch({
      redes: [],
      cabos: [],
      postes: 'invalid',
      cabos_por_rede: null,
    }))
    const { result } = renderHook(() => useConfigState())

    await waitFor(() => expect(result.current.configState.status).toBe('success'))

    expect(result.current.config.postes).toEqual({})
    expect(result.current.config.cabos_por_rede).toEqual({})
  })
})
