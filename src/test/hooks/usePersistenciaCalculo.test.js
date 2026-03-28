/**
 * Tests for usePersistenciaCalculo — Gate 3: critical domain error blocking.
 *
 * Gate 3 requirement: release must be automatically blocked when there is an
 * unmitigated critical domain error in calculation/persistence.
 *
 * Proofs:
 *   1. 403/FORBIDDEN → isForbidden=true, no auto-retry, canNextPoint blocked.
 *   2. MAX_RETRIES exhausted → terminal error, canRetry=true, canNextPoint blocked.
 *   3. 200 success → status='saved' (canNextPoint enabled).
 *
 * All tests mock global.fetch so the real requestJson / persistCalculo pipeline
 * runs with controlled HTTP responses (avoids ES-module path issues with vi.mock).
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import usePersistenciaCalculo from '@/hooks/usePersistenciaCalculo'

// ─── Shared fixtures ──────────────────────────────────────────────────────────

const PONTO_ID = 'ponto-001'
const LAST_PAYLOAD = {
  mt1: [], mt2: [], bt: [], btz: [], ral: [],
  poste: { tipoPoste: 'CC', modeloPoste: '11/200' },
}
const RESULTADO = {
  status_poste: 'OK',
  total_tracao_dan: 120,
  mt1: { travessias: [] },
  mt2: { travessias: [] },
  bt: { travessias: [] },
  btz: { travessias: [] },
  ral: { travessias: [] },
}

// ─── Fetch mock factories (fresh Response per call) ──────────────────────────

function ok200() {
  return Promise.resolve(new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  }))
}

function forbidden403() {
  return Promise.resolve(new Response(JSON.stringify({ detail: 'Acesso negado' }), {
    status: 403,
    headers: { 'Content-Type': 'application/json' },
  }))
}

function serverError500() {
  return Promise.resolve(new Response(JSON.stringify({ detail: 'Server error' }), {
    status: 500,
    headers: { 'Content-Type': 'application/json' },
  }))
}

// ─── Setup / teardown ────────────────────────────────────────────────────────

let fetchMock

beforeEach(() => {
  fetchMock = vi.fn()
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.clearAllTimers()
})

// ─── Hook render helpers ──────────────────────────────────────────────────────

/** autoSave=true: hook schedules persistence automatically (initial waitMs=0). */
function renderAutoSave() {
  return renderHook(() =>
    usePersistenciaCalculo({
      pontoId: PONTO_ID,
      lastPayload: LAST_PAYLOAD,
      resultado: RESULTADO,
      autoSave: true,
    })
  )
}

/** autoSave=false: caller controls when flushPersistQueue() runs. */
function renderManual() {
  return renderHook(() =>
    usePersistenciaCalculo({
      pontoId: PONTO_ID,
      lastPayload: LAST_PAYLOAD,
      resultado: RESULTADO,
      autoSave: false,
    })
  )
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('usePersistenciaCalculo — Gate 3: critical domain error blocking', () => {

  // ── 403 / FORBIDDEN ────────────────────────────────────────────────────────

  describe('403 (FORBIDDEN) error path', () => {
    it('sets isForbidden=true when the server returns 403', async () => {
      fetchMock.mockImplementation(forbidden403)

      const { result } = renderAutoSave()

      await waitFor(() => expect(result.current.persistencia.status).toBe('error'), { timeout: 3000 })
      expect(result.current.persistencia.isForbidden).toBe(true)
    })

    it('does NOT schedule an auto-retry after 403 (willRetry=false)', async () => {
      fetchMock.mockImplementation(forbidden403)

      const { result } = renderAutoSave()

      await waitFor(() => expect(result.current.persistencia.isForbidden).toBe(true), { timeout: 3000 })
      expect(result.current.persistencia.willRetry).toBe(false)
    })

    it('keeps canRetry=true after 403 for manual operator retry', async () => {
      fetchMock.mockImplementation(forbidden403)

      const { result } = renderAutoSave()

      await waitFor(() => expect(result.current.persistencia.status).toBe('error'), { timeout: 3000 })
      expect(result.current.persistencia.canRetry).toBe(true)
    })

    it('blocks canNextPoint (status != saved) after a 403', async () => {
      fetchMock.mockImplementation(forbidden403)

      const { result } = renderAutoSave()

      await waitFor(() => expect(result.current.persistencia.status).toBe('error'), { timeout: 3000 })
      // App derives: canNextPoint = persistencia.status === 'saved'
      expect(result.current.persistencia.status).not.toBe('saved')
    })

    it('fetch is called exactly once — no auto-retry loop after 403', async () => {
      fetchMock
        .mockImplementationOnce(forbidden403)
        .mockImplementation(ok200)   // guard for stray calls

      const { result } = renderAutoSave()

      await waitFor(() => expect(result.current.persistencia.isForbidden).toBe(true), { timeout: 3000 })
      expect(fetchMock).toHaveBeenCalledTimes(1)
    })
  })

  // ── MAX_RETRIES exhausted (manual flush) ─────────────────────────────────
  //
  // We use autoSave=false and call flushPersistQueue() manually 4 times.
  // Each call clears any internally-scheduled retry timer (clearPersistTimer at
  // the top of flushPersistQueue), so no real/fake timer delays are needed.
  // This avoids the setInterval countdown accumulation that causes OOM with
  // fake timers.

  describe('MAX_RETRIES exhausted path', () => {
    it('enters terminal error state after 3 transient failures', async () => {
      // 4 transient failures: initial + retries 1, 2, 3 (MAX_RETRIES=3)
      fetchMock
        .mockImplementationOnce(serverError500)
        .mockImplementationOnce(serverError500)
        .mockImplementationOnce(serverError500)
        .mockImplementationOnce(serverError500)
        .mockImplementation(ok200)  // guard

      const { result } = renderManual()

      // Wait for the first useEffect to populate pendingPersistRef
      await act(async () => {})

      // Manually flush 4 times; each flush clears any internally-scheduled timer
      for (let i = 0; i < 4; i++) {
        await act(async () => { await result.current.flushPersistQueue() })
      }

      expect(fetchMock).toHaveBeenCalledTimes(4)
      expect(result.current.persistencia.status).toBe('error')
      expect(result.current.persistencia.willRetry).toBe(false)
      expect(result.current.persistencia.canRetry).toBe(true)
      expect(result.current.persistencia.isForbidden).toBe(false)
    })

    it('blocks canNextPoint (status != saved) when retries are exhausted', async () => {
      fetchMock
        .mockImplementationOnce(serverError500)
        .mockImplementationOnce(serverError500)
        .mockImplementationOnce(serverError500)
        .mockImplementationOnce(serverError500)
        .mockImplementation(ok200)

      const { result } = renderManual()

      await act(async () => {})

      for (let i = 0; i < 4; i++) {
        await act(async () => { await result.current.flushPersistQueue() })
      }

      expect(result.current.persistencia.status).not.toBe('saved')
    })
  })

  // ── Happy path ─────────────────────────────────────────────────────────────

  describe('happy path', () => {
    it('reaches status=saved after a 200 response', async () => {
      fetchMock.mockImplementation(ok200)

      const { result } = renderAutoSave()

      await waitFor(() => expect(result.current.persistencia.status).toBe('saved'), { timeout: 3000 })
      expect(result.current.persistencia.isForbidden).toBe(false)
      expect(result.current.persistencia.willRetry).toBe(false)
    })

    it('canNextPoint derivation: status===saved satisfies the condition', async () => {
      fetchMock.mockImplementation(ok200)

      const { result } = renderAutoSave()

      await waitFor(() => expect(result.current.persistencia.status).toBe('saved'), { timeout: 3000 })
      // App-level: canNextPoint = persistencia.status === 'saved'
      expect(result.current.persistencia.status === 'saved').toBe(true)
    })
  })

  // ── resetPersistencia ──────────────────────────────────────────────────────

  describe('resetPersistencia', () => {
    it('clears a critical 403 error state back to idle', async () => {
      fetchMock.mockImplementation(forbidden403)

      const { result } = renderAutoSave()

      await waitFor(() => expect(result.current.persistencia.isForbidden).toBe(true), { timeout: 3000 })

      result.current.resetPersistencia()

      await waitFor(() => expect(result.current.persistencia.status).toBe('idle'), { timeout: 1000 })
      expect(result.current.persistencia.isForbidden).toBe(false)
      expect(result.current.persistencia.canRetry).toBe(false)
    })
  })
})
