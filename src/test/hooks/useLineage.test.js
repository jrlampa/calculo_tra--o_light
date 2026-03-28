/**
 * Tests for useLineage hook.
 *
 * - Does nothing when no posteId or origemId is provided.
 * - Fetches lineage chain when both are present.
 * - Exposes loading / error states.
 * - Clears chain when posteId is reset.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useLineage } from '@/hooks/useLineage'

// Mock the API module
vi.mock('@/services/calculoApi', () => ({
  obterLinhagem: vi.fn(),
}))

import { obterLinhagem } from '@/services/calculoApi'

const CHAIN = [
  { id: 'a', numero: '7', tipo_poste: 'DT', modelo_poste: '9m', projeto_id: 'p1', atualizado_em: '2025-01-01T00:00:00Z', calculos_count: 2 },
  { id: 'b', numero: '7', tipo_poste: 'DT', modelo_poste: '9m', projeto_id: 'p2', atualizado_em: '2026-01-01T00:00:00Z', calculos_count: 1 },
]

describe('useLineage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns empty chain and does not fetch when origemId is null', () => {
    const { result } = renderHook(() => useLineage('some-id', null))
    expect(obterLinhagem).not.toHaveBeenCalled()
    expect(result.current.chain).toEqual([])
    expect(result.current.loading).toBe(false)
  })

  it('returns empty chain and does not fetch when posteId is null', () => {
    const { result } = renderHook(() => useLineage(null, 'some-origem'))
    expect(obterLinhagem).not.toHaveBeenCalled()
    expect(result.current.chain).toEqual([])
  })

  it('fetches lineage when both ids are provided', async () => {
    obterLinhagem.mockResolvedValueOnce({ chain: CHAIN, profundidade: 2 })
    const { result } = renderHook(() => useLineage('b', 'a'))
    expect(result.current.loading).toBe(true)
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(obterLinhagem).toHaveBeenCalledWith('b')
    expect(result.current.chain).toHaveLength(2)
    expect(result.current.profundidade).toBe(2)
  })

  it('exposes error when fetch fails', async () => {
    obterLinhagem.mockRejectedValueOnce(new Error('Network error'))
    const { result } = renderHook(() => useLineage('b', 'a'))
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.error).toBe('Network error')
    expect(result.current.chain).toEqual([])
  })

  it('clears chain when origemId becomes null', async () => {
    obterLinhagem.mockResolvedValueOnce({ chain: CHAIN, profundidade: 2 })
    const { result, rerender } = renderHook(
      ({ pid, oid }) => useLineage(pid, oid),
      { initialProps: { pid: 'b', oid: 'a' } }
    )
    await waitFor(() => expect(result.current.chain).toHaveLength(2))
    rerender({ pid: null, oid: null })
    await waitFor(() => expect(result.current.chain).toEqual([]))
    expect(result.current.profundidade).toBe(0)
  })
})
