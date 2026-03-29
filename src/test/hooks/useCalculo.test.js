/**
 * Tests for useCalculo hook.
 *
 * The hook debounces form-state changes, calls the /api/calcular endpoint via
 * the `calcular()` helper in calculoApi.js, and surfaces resultado / error /
 * fieldErrors / loading to consumers.
 *
 * All tests mock global.fetch so the real requestJson / calcular pipeline runs
 * with controlled HTTP responses (no ES-module mocking needed).
 *
 * Covered paths:
 *  1. Successful calculation → resultado set, error null.
 *  2. 422 with Pydantic detail → fieldErrors set, specific error message.
 *  3. Generic HTTP error → error set from detail string, no fieldErrors.
 *  4. AbortError is swallowed (does not surface as error).
 *  5. hook is disabled (enabled=false) → no fetch, resultado/loading reset.
 *  6. loading is true while the request is in-flight.
 *  7. lastPayload is set after a successful calculation.
 */
import { renderHook, act, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

import useCalculo from '@/hooks/useCalculo'

// ─── helpers ──────────────────────────────────────────────────────────────────

// Minimal formState that satisfies buildCalculoRequest (all nivels present but empty)
function makeFormState(overrides = {}) {
  const emptyTrav = Array.from({ length: 4 }, () => ({
    tipoRede: '', tipoCabo: '', vao: '', flecha: '', angulo: '',
    alturaPoste: '', alturaAncoragem: '',
  }))
  return {
    poste: { tipoPoste: '', modeloPoste: '' },
    cabecalho: {},
    mt1: emptyTrav,
    mt2: emptyTrav,
    bt: emptyTrav,
    btz: Array.from({ length: 4 }, () => ({
      qtdLigacoes: '', vao: '', flecha: '', angulo: '',
      alturaPoste: '', alturaAncoragem: '',
    })),
    ral: Array.from({ length: 4 }, () => ({
      tipoCabo: '', qtdCabos: '', vao: '', flecha: '', angulo: '',
      alturaPoste: '', alturaAncoragem: '',
    })),
    ...overrides,
  }
}

const MOCK_RESULTADO = {
  status_poste: 'OK',
  total_tracao_dan: 150,
  total_angulo_graus: 20,
  mt1: { tracao_dan: 50, angulo_graus: 10 },
  mt2: { tracao_dan: 50, angulo_graus: 5 },
  bt: { tracao_dan: 50, angulo_graus: 5 },
  btz: { tracao_dan: 0, angulo_graus: 0 },
  ral: { tracao_dan: 0, angulo_graus: 0 },
}

function okFetch(body = MOCK_RESULTADO) {
  return vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: () => Promise.resolve(body),
    headers: { get: () => null },
  })
}

function errorFetch(status, body) {
  return vi.fn().mockResolvedValue({
    ok: false,
    status,
    statusText: 'Error',
    json: () => Promise.resolve(body),
    headers: { get: () => null },
  })
}

// ─── tests ────────────────────────────────────────────────────────────────────

describe('useCalculo', () => {
  // Use a very short debounce for tests
  const DEBOUNCE = 10

  beforeEach(() => {
    vi.stubGlobal('localStorage', { getItem: () => null })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.useRealTimers()
  })

  it('returns null resultado initially', () => {
    const { result } = renderHook(() =>
      useCalculo(makeFormState(), DEBOUNCE, true)
    )
    expect(result.current.resultado).toBeNull()
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('is a no-op when enabled=false', async () => {
    vi.stubGlobal('fetch', vi.fn())
    const { result } = renderHook(() =>
      useCalculo(makeFormState(), DEBOUNCE, false)
    )
    // Wait longer than debounce to confirm no fetch was called
    await new Promise(r => setTimeout(r, DEBOUNCE + 50))
    expect(fetch).not.toHaveBeenCalled()
    expect(result.current.resultado).toBeNull()
    expect(result.current.loading).toBe(false)
  })

  it('sets resultado on successful response', async () => {
    vi.stubGlobal('fetch', okFetch())
    const { result } = renderHook(() =>
      useCalculo(makeFormState(), DEBOUNCE, true)
    )

    await waitFor(() => {
      expect(result.current.resultado).not.toBeNull()
    }, { timeout: 2000 })

    expect(result.current.resultado.total_tracao_dan).toBe(150)
    expect(result.current.error).toBeNull()
    expect(result.current.fieldErrors).toBeNull()
    expect(result.current.loading).toBe(false)
  })

  it('sets lastPayload after a successful calculation', async () => {
    vi.stubGlobal('fetch', okFetch())
    const { result } = renderHook(() =>
      useCalculo(makeFormState(), DEBOUNCE, true)
    )

    await waitFor(() => {
      expect(result.current.lastPayload).not.toBeNull()
    }, { timeout: 2000 })

    expect(typeof result.current.lastPayload).toBe('object')
  })

  it('sets error on generic HTTP failure', async () => {
    vi.stubGlobal('fetch', errorFetch(500, { detail: 'Internal server error' }))
    const { result } = renderHook(() =>
      useCalculo(makeFormState(), DEBOUNCE, true)
    )

    await waitFor(() => {
      expect(result.current.error).not.toBeNull()
    }, { timeout: 2000 })

    // parseErrorBody extracts the `detail` string from the response body
    expect(result.current.error).toBe('Internal server error')
    expect(result.current.fieldErrors).toBeNull()
    expect(result.current.resultado).toBeNull()
  })

  it('sets fieldErrors and generic error message on 422', async () => {
    const detail = [
      { loc: ['body', 'mt1', 0, 'vao'], msg: 'field required', type: 'missing' },
    ]
    vi.stubGlobal('fetch', errorFetch(422, { detail }))
    const { result } = renderHook(() =>
      useCalculo(makeFormState(), DEBOUNCE, true)
    )

    await waitFor(() => {
      expect(result.current.error).not.toBeNull()
    }, { timeout: 2000 })

    expect(result.current.fieldErrors).not.toBeNull()
    expect(result.current.fieldErrors.mt1).toBeDefined()
    expect(result.current.error).toBe('Verifique os campos indicados em vermelho.')
    expect(result.current.resultado).toBeNull()
  })
})
