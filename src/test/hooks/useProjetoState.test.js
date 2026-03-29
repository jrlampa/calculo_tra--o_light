/**
 * Tests for useProjetoState hook.
 *
 * Covered paths:
 *  1. Initial state — etapa='home', cabecalho empty, projetoAtual=null.
 *  2. handleHeader — updates cabecalho field.
 *  3. canConfirmProjeto — false when projeto empty or loading.
 *  4. handleIniciarNovoProjeto — resets projetoAtual, sets etapa='projeto'.
 *  5. handleConfirmProjeto — blank projeto → sets error; valid → etapa='calculo'.
 *  6. handleAbrirProjeto — populates cabecalho from projeto, etapa='calculo'.
 *  7. handleEditarProjeto — populates cabecalho from projeto, etapa='projeto'.
 *  8. handleGuestConfirm — sets localStorage guest_mode, etapa='calculo'.
 *  9. resetProjeto — returns to home state.
 * 10. handleExcluirProjeto — calls deleteProjeto via calculoApi.
 */
import { renderHook, act, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

import { useProjetoState } from '@/hooks/useProjetoState'

// ─── helpers ──────────────────────────────────────────────────────────────────

const SAMPLE_PROJETO = {
  id: 'proj-001',
  orgao: 'LIGHT S.A.',
  ns: 'LT-RJ-001',
  nome: 'Projeto Teste',
  endereco: 'Rua X, 100',
  estudado_por: 'João',
  matricula: '12345',
  data_estudo: '2025-01-01',
}

// ─── tests ────────────────────────────────────────────────────────────────────

describe('useProjetoState', () => {
  let localStorageMock

  beforeEach(() => {
    localStorageMock = { getItem: vi.fn(() => null), setItem: vi.fn() }
    vi.stubGlobal('localStorage', localStorageMock)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.resetAllMocks()
  })

  // ── 1. initial state ───────────────────────────────────────────────────────

  it('starts with etapa=home, empty cabecalho, no projetoAtual', () => {
    const { result } = renderHook(() => useProjetoState())
    expect(result.current.etapa).toBe('home')
    expect(result.current.projetoAtual).toBeNull()
    expect(result.current.cabecalho.projeto).toBe('')
  })

  // ── 2. handleHeader ────────────────────────────────────────────────────────

  it('handleHeader updates the specified cabecalho field', () => {
    const { result } = renderHook(() => useProjetoState())

    act(() => {
      result.current.handlers.handleHeader('projeto', 'Novo Projeto')
    })

    expect(result.current.cabecalho.projeto).toBe('Novo Projeto')
  })

  it('handleHeader updates multiple fields independently', () => {
    const { result } = renderHook(() => useProjetoState())

    act(() => {
      result.current.handlers.handleHeader('orgao', 'ENEL')
      result.current.handlers.handleHeader('ns', 'EN-001')
    })

    expect(result.current.cabecalho.orgao).toBe('ENEL')
    expect(result.current.cabecalho.ns).toBe('EN-001')
  })

  // ── 3. canConfirmProjeto ───────────────────────────────────────────────────

  it('canConfirmProjeto is falsy when projeto is empty', () => {
    const { result } = renderHook(() => useProjetoState())
    expect(result.current.canConfirmProjeto).toBeFalsy()
  })

  it('canConfirmProjeto is truthy when projeto has a name', () => {
    const { result } = renderHook(() => useProjetoState())

    act(() => {
      result.current.handlers.handleHeader('projeto', 'Meu Projeto')
    })

    expect(result.current.canConfirmProjeto).toBeTruthy()
  })

  it('canConfirmProjeto is falsy for whitespace-only projeto name', () => {
    const { result } = renderHook(() => useProjetoState())

    act(() => {
      result.current.handlers.handleHeader('projeto', '   ')
    })

    expect(result.current.canConfirmProjeto).toBeFalsy()
  })

  // ── 4. handleIniciarNovoProjeto ────────────────────────────────────────────

  it('handleIniciarNovoProjeto clears projetoAtual and goes to etapa=projeto', () => {
    const { result } = renderHook(() => useProjetoState())

    // Simulate we already have a projeto
    act(() => {
      result.current.handlers.handleEditarProjeto(SAMPLE_PROJETO)
    })
    expect(result.current.projetoAtual).not.toBeNull()

    act(() => {
      result.current.handlers.handleIniciarNovoProjeto()
    })

    expect(result.current.projetoAtual).toBeNull()
    expect(result.current.etapa).toBe('projeto')
  })

  // ── 5. handleConfirmProjeto ────────────────────────────────────────────────

  it('handleConfirmProjeto sets error when projeto is empty', async () => {
    const { result } = renderHook(() => useProjetoState())

    await act(async () => {
      await result.current.handlers.handleConfirmProjeto()
    })

    expect(result.current.projetoState.error).toMatch(/nome do projeto/)
    expect(result.current.etapa).toBe('home')
  })

  it('handleConfirmProjeto advances to etapa=calculo when projeto is set', async () => {
    const { result } = renderHook(() => useProjetoState())

    act(() => {
      result.current.handlers.handleHeader('projeto', 'Projeto Valid')
    })

    await act(async () => {
      await result.current.handlers.handleConfirmProjeto()
    })

    expect(result.current.etapa).toBe('calculo')
  })

  // ── 6. handleAbrirProjeto ──────────────────────────────────────────────────

  it('handleAbrirProjeto populates cabecalho from projeto and goes to calculo', async () => {
    const { result } = renderHook(() => useProjetoState())

    await act(async () => {
      await result.current.handlers.handleAbrirProjeto(SAMPLE_PROJETO)
    })

    expect(result.current.etapa).toBe('calculo')
    expect(result.current.projetoAtual).toBe(SAMPLE_PROJETO)
    expect(result.current.cabecalho.orgao).toBe('LIGHT S.A.')
    expect(result.current.cabecalho.ns).toBe('LT-RJ-001')
    expect(result.current.cabecalho.projeto).toBe('Projeto Teste')
    expect(result.current.cabecalho.ponto).toBe('')
    expect(result.current.projetoState.loading).toBe(false)
  })

  // ── 7. handleEditarProjeto ─────────────────────────────────────────────────

  it('handleEditarProjeto populates cabecalho and goes to etapa=projeto', () => {
    const { result } = renderHook(() => useProjetoState())

    act(() => {
      result.current.handlers.handleEditarProjeto(SAMPLE_PROJETO)
    })

    expect(result.current.etapa).toBe('projeto')
    expect(result.current.projetoAtual).toBe(SAMPLE_PROJETO)
    expect(result.current.cabecalho.projeto).toBe('Projeto Teste')
    expect(result.current.cabecalho.matricula).toBe('12345')
  })

  // ── 8. handleGuestConfirm ──────────────────────────────────────────────────

  it('handleGuestConfirm sets guest_mode in localStorage and goes to calculo', async () => {
    const { result } = renderHook(() => useProjetoState())

    await act(async () => {
      await result.current.handlers.handleGuestConfirm()
    })

    expect(localStorageMock.setItem).toHaveBeenCalledWith('guest_mode', 'true')
    expect(result.current.etapa).toBe('calculo')
  })

  // ── 9. resetProjeto ────────────────────────────────────────────────────────

  it('resetProjeto restores home state', async () => {
    const { result } = renderHook(() => useProjetoState())

    // Navigate to calculo first
    act(() => {
      result.current.handlers.handleEditarProjeto(SAMPLE_PROJETO)
    })

    act(() => {
      result.current.handlers.resetProjeto()
    })

    expect(result.current.etapa).toBe('home')
    expect(result.current.projetoAtual).toBeNull()
    expect(result.current.cabecalho.projeto).toBe('')
    expect(result.current.projetoState.loading).toBe(false)
    expect(result.current.projetoState.error).toBe('')
  })

  // ── 10. handleExcluirProjeto ───────────────────────────────────────────────

  it('handleExcluirProjeto calls deleteProjeto via fetch', async () => {
    // deleteProjeto calls fetch under the hood
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 204,
      json: () => Promise.resolve(null),
      headers: { get: () => null },
    }))
    const { result } = renderHook(() => useProjetoState())

    await act(async () => {
      await result.current.handlers.handleExcluirProjeto('proj-001')
    })

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/projetos/proj-001'),
      expect.objectContaining({ method: 'DELETE' })
    )
  })
})
