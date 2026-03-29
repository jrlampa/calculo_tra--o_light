/**
 * Tests for usePontoState hook.
 *
 * Covered paths:
 *  1. Initial state — empty poste, null pontoAtual, status='idle'.
 *  2. handlePoste — updates tipoPoste/modeloPoste fields.
 *  3. handlePoste changing tipoPoste clears modeloPoste (type changed).
 *  4. handlePoste changing tipoPoste to same value preserves modeloPoste.
 *  5. canConfirmPonto is false without projetoAtual.id.
 *  6. canConfirmPonto is false without ponto in cabecalho.
 *  7. canConfirmPonto is false without tipoPoste/modeloPoste.
 *  8. canConfirmPonto is true when all conditions met.
 *  9. handleConfirmPonto: error when projetoAtual has no id.
 * 10. handleConfirmPonto: error when ponto empty.
 * 11. handleConfirmPonto: error when tipoPoste/modeloPoste missing.
 * 12. handleConfirmPonto: success — sets pontoAtual and status='saved'.
 * 13. handleClonarDeOutroProjeto: error when projetoAtual has no id.
 * 14. handleClonarDeOutroProjeto: success — sets pontoAtual and origemId.
 * 15. resetPonto — clears all state back to initial.
 * 16. handleProximoPonto — clears ponto data but keeps project.
 * 17. headerFeedback reflects various states.
 * 18. Changing cabecalho.ponto triggers resetPonto via effect.
 */
import { renderHook, act, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

import { usePontoState } from '@/hooks/usePontoState'

// ─── helpers ──────────────────────────────────────────────────────────────────

const PROJETO = { id: 'proj-001' }

const PONTO_CRIADO = {
  id: 'ponto-abc',
  numero: 'P-01',
  tipo_poste: 'Concreto',
  modelo_poste: '11/200',
  origem_id: null,
}

const PONTO_CLONADO = {
  id: 'ponto-clone',
  numero: 'P-02',
  tipo_poste: 'Aço',
  modelo_poste: '11/300',
  origem_id: 'original-poste-id',
}

function renderPonto(cabecalhoOverride = {}, projetoOverride = PROJETO) {
  const cabecalho = { ponto: 'P-01', ...cabecalhoOverride }
  const projetoAtual = projetoOverride
  const resetPersistencia = vi.fn()

  return renderHook(() =>
    usePontoState({ projetoAtual, cabecalho, resetPersistencia })
  )
}

// ─── tests ────────────────────────────────────────────────────────────────────

describe('usePontoState', () => {
  beforeEach(() => {
    vi.stubGlobal('localStorage', { getItem: vi.fn(), setItem: vi.fn() })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.resetAllMocks()
  })

  // ── 1. Initial state ───────────────────────────────────────────────────────

  it('starts with empty poste and idle status', () => {
    const { result } = renderPonto()
    expect(result.current.poste.tipoPoste).toBe('')
    expect(result.current.poste.modeloPoste).toBe('')
    expect(result.current.pontoAtual).toBeNull()
    expect(result.current.pontoState.status).toBe('idle')
    expect(result.current.origemId).toBeNull()
  })

  // ── 2. handlePoste ─────────────────────────────────────────────────────────

  it('handlePoste updates modeloPoste', () => {
    const { result } = renderPonto()

    act(() => {
      result.current.handlers.handlePoste('tipoPoste', 'Concreto')
      result.current.handlers.handlePoste('modeloPoste', '11/200')
    })

    expect(result.current.poste.tipoPoste).toBe('Concreto')
    expect(result.current.poste.modeloPoste).toBe('11/200')
  })

  // ── 3. Changing tipoPoste clears modeloPoste ───────────────────────────────

  it('changing tipoPoste to a different value clears modeloPoste', () => {
    const { result } = renderPonto()

    act(() => {
      result.current.handlers.handlePoste('tipoPoste', 'Concreto')
      result.current.handlers.handlePoste('modeloPoste', '11/200')
    })
    expect(result.current.poste.modeloPoste).toBe('11/200')

    act(() => {
      result.current.handlers.handlePoste('tipoPoste', 'Aço')
    })
    expect(result.current.poste.modeloPoste).toBe('')
  })

  // ── 4. Same tipoPoste preserves modeloPoste ───────────────────────────────

  it('setting tipoPoste to same value preserves modeloPoste', () => {
    const { result } = renderPonto()

    act(() => {
      result.current.handlers.handlePoste('tipoPoste', 'Concreto')
      result.current.handlers.handlePoste('modeloPoste', '11/200')
    })

    act(() => {
      result.current.handlers.handlePoste('tipoPoste', 'Concreto')
    })

    expect(result.current.poste.modeloPoste).toBe('11/200')
  })

  // ── 5–8. canConfirmPonto ────────────────────────────────────────────────────

  it('canConfirmPonto is false without projetoAtual', () => {
    const { result } = renderPonto({}, null)
    expect(result.current.canConfirmPonto).toBe(false)
  })

  it('canConfirmPonto is false without ponto in cabecalho', () => {
    const { result } = renderPonto({ ponto: '' })
    expect(result.current.canConfirmPonto).toBe(false)
  })

  it('canConfirmPonto is false without tipoPoste/modeloPoste', () => {
    const { result } = renderPonto()
    expect(result.current.canConfirmPonto).toBe(false)
  })

  it('canConfirmPonto is true when all conditions are met and no pontoAtual', () => {
    const { result } = renderPonto({ ponto: 'P-01' })

    act(() => {
      result.current.handlers.handlePoste('tipoPoste', 'Concreto')
      result.current.handlers.handlePoste('modeloPoste', '11/200')
    })

    expect(result.current.canConfirmPonto).toBe(true)
  })

  // ── 9–11. handleConfirmPonto validation errors ─────────────────────────────

  it('handleConfirmPonto sets error when projetoAtual has no id', async () => {
    const { result } = renderPonto({}, { id: null })

    await act(async () => {
      await result.current.handlers.handleConfirmPonto()
    })

    expect(result.current.pontoState.status).toBe('error')
    expect(result.current.pontoState.error).toMatch(/projeto/i)
  })

  it('handleConfirmPonto sets error when ponto is empty', async () => {
    const { result } = renderPonto({ ponto: '' }, PROJETO)

    await act(async () => {
      await result.current.handlers.handleConfirmPonto()
    })

    expect(result.current.pontoState.status).toBe('error')
    expect(result.current.pontoState.error).toMatch(/ponto/i)
  })

  it('handleConfirmPonto sets error when tipoPoste/modeloPoste missing', async () => {
    const { result } = renderPonto({ ponto: 'P-01' }, PROJETO)

    await act(async () => {
      await result.current.handlers.handleConfirmPonto()
    })

    expect(result.current.pontoState.status).toBe('error')
    expect(result.current.pontoState.error).toMatch(/tipo.*modelo|modelo.*tipo/i)
  })

  // ── 12. handleConfirmPonto success ─────────────────────────────────────────

  it('handleConfirmPonto saves ponto on success', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: () => Promise.resolve(PONTO_CRIADO),
      headers: { get: () => null },
    }))

    const { result } = renderPonto({ ponto: 'P-01' })

    act(() => {
      result.current.handlers.handlePoste('tipoPoste', 'Concreto')
      result.current.handlers.handlePoste('modeloPoste', '11/200')
    })

    await act(async () => {
      await result.current.handlers.handleConfirmPonto()
    })

    await waitFor(() => {
      expect(result.current.pontoAtual?.id).toBe('ponto-abc')
      expect(result.current.pontoState.status).toBe('saved')
    })
  })

  // ── 13. handleClonarDeOutroProjeto: no project id ─────────────────────────

  it('handleClonarDeOutroProjeto sets error when projetoAtual has no id', async () => {
    const { result } = renderPonto({}, { id: null })

    await act(async () => {
      await result.current.handlers.handleClonarDeOutroProjeto('some-poste-id')
    })

    expect(result.current.pontoState.status).toBe('error')
    expect(result.current.pontoState.error).toMatch(/projeto/i)
  })

  // ── 14. handleClonarDeOutroProjeto success ────────────────────────────────

  it('handleClonarDeOutroProjeto sets cloned ponto and origemId', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(PONTO_CLONADO),
      headers: { get: () => null },
    }))

    // cabecalho.ponto must match cloned poste's numero so the cleanup effect
    // does NOT immediately reset pontoAtual after the clone
    const { result } = renderHook(() =>
      usePontoState({
        projetoAtual: PROJETO,
        cabecalho: { ponto: 'P-02' },
        resetPersistencia: vi.fn(),
      })
    )

    await act(async () => {
      await result.current.handlers.handleClonarDeOutroProjeto('original-poste-id')
    })

    await waitFor(() => {
      expect(result.current.pontoAtual?.id).toBe('ponto-clone')
      expect(result.current.origemId).toBe('original-poste-id')
      expect(result.current.poste.tipoPoste).toBe('Aço')
    })
  })

  // ── 15. resetPonto ────────────────────────────────────────────────────────

  it('resetPonto clears all state', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: () => Promise.resolve(PONTO_CRIADO),
      headers: { get: () => null },
    }))

    const { result } = renderPonto({ ponto: 'P-01' })

    act(() => {
      result.current.handlers.handlePoste('tipoPoste', 'Concreto')
      result.current.handlers.handlePoste('modeloPoste', '11/200')
    })

    await act(async () => {
      await result.current.handlers.handleConfirmPonto()
    })

    await waitFor(() => expect(result.current.pontoAtual?.id).toBe('ponto-abc'))

    act(() => {
      result.current.handlers.resetPonto()
    })

    expect(result.current.pontoAtual).toBeNull()
    expect(result.current.poste.tipoPoste).toBe('')
    expect(result.current.pontoState.status).toBe('idle')
    expect(result.current.origemId).toBeNull()
  })

  // ── 16. handleProximoPonto ─────────────────────────────────────────────────

  it('handleProximoPonto clears ponto and calls resetPersistencia', async () => {
    const resetPersistencia = vi.fn()
    const { result } = renderHook(() =>
      usePontoState({ projetoAtual: PROJETO, cabecalho: { ponto: 'P-01' }, resetPersistencia })
    )

    act(() => {
      result.current.handlers.handleProximoPonto()
    })

    expect(result.current.pontoAtual).toBeNull()
    expect(result.current.poste.tipoPoste).toBe('')
    expect(resetPersistencia).toHaveBeenCalled()
  })

  // ── 17. headerFeedback ─────────────────────────────────────────────────────

  it('headerFeedback asks for ponto when ponto is empty', () => {
    const { result } = renderPonto({ ponto: '' })
    expect(result.current.headerFeedback.tone).toBe('idle')
    expect(result.current.headerFeedback.message).toMatch(/ponto/i)
  })

  it('headerFeedback asks for poste when ponto is set but no tipoPoste', () => {
    const { result } = renderPonto({ ponto: 'P-01' })
    expect(result.current.headerFeedback.tone).toBe('idle')
    expect(result.current.headerFeedback.message).toMatch(/tipo.*modelo|modelo.*tipo/i)
  })

  it('headerFeedback shows saved tone when ponto confirmed', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: () => Promise.resolve(PONTO_CRIADO),
      headers: { get: () => null },
    }))

    const { result } = renderPonto({ ponto: 'P-01' })

    act(() => {
      result.current.handlers.handlePoste('tipoPoste', 'Concreto')
      result.current.handlers.handlePoste('modeloPoste', '11/200')
    })

    await act(async () => {
      await result.current.handlers.handleConfirmPonto()
    })

    await waitFor(() => {
      expect(result.current.headerFeedback.tone).toBe('saved')
    })
  })

  // ── 18. ponto change triggers reset ───────────────────────────────────────

  it('changing ponto in cabecalho resets the ponto state after confirmation', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: () => Promise.resolve(PONTO_CRIADO),
      headers: { get: () => null },
    }))

    let cabecalho = { ponto: 'P-01' }
    const { result, rerender } = renderHook(
      ({ cab }) => usePontoState({ projetoAtual: PROJETO, cabecalho: cab, resetPersistencia: vi.fn() }),
      { initialProps: { cab: cabecalho } }
    )

    act(() => {
      result.current.handlers.handlePoste('tipoPoste', 'Concreto')
      result.current.handlers.handlePoste('modeloPoste', '11/200')
    })

    await act(async () => {
      await result.current.handlers.handleConfirmPonto()
    })

    await waitFor(() => expect(result.current.pontoAtual?.id).toBe('ponto-abc'))

    // Change ponto name → should reset pontoAtual via effect
    rerender({ cab: { ponto: 'P-02' } })

    await waitFor(() => {
      expect(result.current.pontoAtual).toBeNull()
    })
  })
})
