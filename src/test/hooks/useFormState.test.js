/* Tests for useFormState:
 * - restoreFormSnapshot restores all levels atomically
 * - restoreFormSnapshot is a no-op when called with null/undefined
 * - handleTravessiaChange updates the correct cell
 * - resetForm zeroes out all cells
 */
import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useFormState } from '@/hooks/useFormState'

// Helper: build a valid MT snapshot row
function makeMTRow(overrides = {}) {
  return { tipoRede: '', tipoCabo: '', vao: '', flecha: '', angulo: '', alturaPoste: '', alturaAncoragem: '', ...overrides }
}
// Helper: build a valid BTZ snapshot row
function makeBTZRow(overrides = {}) {
  return { qtdLigacoes: '', vao: '', flecha: '', angulo: '', alturaPoste: '', alturaAncoragem: '', ...overrides }
}
// Helper: build a valid RAL snapshot row
function makeRALRow(overrides = {}) {
  return { tipoCabo: '', qtdCabos: '', vao: '', flecha: '', angulo: '', alturaPoste: '', alturaAncoragem: '', ...overrides }
}

// Build a complete form snapshot
function makeSnapshot(overrides = {}) {
  return {
    mt1: [makeMTRow({ tipoRede: 'SNAP-MT1', tipoCabo: 'CAB-A', vao: '100' }), makeMTRow(), makeMTRow(), makeMTRow()],
    mt2: [makeMTRow(), makeMTRow(), makeMTRow(), makeMTRow()],
    bt:  [makeMTRow(), makeMTRow(), makeMTRow(), makeMTRow()],
    btz: [makeBTZRow(), makeBTZRow(), makeBTZRow(), makeBTZRow()],
    ral: [makeRALRow(), makeRALRow(), makeRALRow(), makeRALRow()],
    ...overrides,
  }
}

describe('useFormState', () => {
  it('initial state has empty travessias with correct shape', () => {
    const { result } = renderHook(() => useFormState())
    const { mt1 } = result.current.travessias
    expect(mt1.length).toBeGreaterThan(0)
    expect(mt1[0].tipoRede).toBe('')
    expect(mt1[0].tipoCabo).toBe('')
  })

  it('handleTravessiaChange updates the correct cell', () => {
    const { result } = renderHook(() => useFormState())

    act(() => {
      result.current.handlers.handleTravessiaChange('mt1', 0, 'tipoRede', 'MT-NOVA')
    })

    expect(result.current.travessias.mt1[0].tipoRede).toBe('MT-NOVA')
    // Other cells remain untouched
    expect(result.current.travessias.mt1[0].tipoCabo).toBe('')
    expect(result.current.travessias.mt2[0].tipoRede).toBe('')
  })

  it('handleTravessiaChange works for btz level', () => {
    const { result } = renderHook(() => useFormState())

    act(() => {
      result.current.handlers.handleTravessiaChange('btz', 1, 'qtdLigacoes', '3')
    })

    expect(result.current.travessias.btz[1].qtdLigacoes).toBe('3')
  })

  it('handleTravessiaChange works for ral level', () => {
    const { result } = renderHook(() => useFormState())

    act(() => {
      result.current.handlers.handleTravessiaChange('ral', 0, 'tipoCabo', 'CAB-RAL')
    })

    expect(result.current.travessias.ral[0].tipoCabo).toBe('CAB-RAL')
  })

  it('resetForm clears all data', () => {
    const { result } = renderHook(() => useFormState())

    act(() => {
      result.current.handlers.handleTravessiaChange('mt1', 0, 'tipoRede', 'PRE-RESET')
      result.current.handlers.handleTravessiaChange('bt', 2, 'tipoCabo', 'PRE-RESET-BT')
    })

    act(() => {
      result.current.handlers.resetForm()
    })

    expect(result.current.travessias.mt1[0].tipoRede).toBe('')
    expect(result.current.travessias.bt[2].tipoCabo).toBe('')
  })

  it('restoreFormSnapshot restores all levels atomically', () => {
    const { result } = renderHook(() => useFormState())
    const snapshot = makeSnapshot()

    act(() => {
      result.current.handlers.restoreFormSnapshot(snapshot)
    })

    expect(result.current.travessias.mt1[0].tipoRede).toBe('SNAP-MT1')
    expect(result.current.travessias.mt1[0].tipoCabo).toBe('CAB-A')
    expect(result.current.travessias.mt1[0].vao).toBe('100')
    // Other levels restored from snapshot (empty rows)
    expect(result.current.travessias.mt2[0].tipoRede).toBe('')
    expect(result.current.travessias.bt[0].tipoRede).toBe('')
  })

  it('restoreFormSnapshot is a no-op for null', () => {
    const { result } = renderHook(() => useFormState())

    act(() => {
      result.current.handlers.handleTravessiaChange('mt1', 0, 'tipoRede', 'BEFORE-NULL')
    })

    act(() => {
      result.current.handlers.restoreFormSnapshot(null)
    })

    // Should not have changed anything
    expect(result.current.travessias.mt1[0].tipoRede).toBe('BEFORE-NULL')
  })

  it('restoreFormSnapshot partial update: only provided levels are restored', () => {
    const { result } = renderHook(() => useFormState())

    act(() => {
      result.current.handlers.handleTravessiaChange('ral', 0, 'tipoCabo', 'RAL-VALUE')
    })

    // Snapshot only overrides mt1 — ral is not in snapshot
    const partialSnapshot = { mt1: makeSnapshot().mt1 }
    act(() => {
      result.current.handlers.restoreFormSnapshot(partialSnapshot)
    })

    expect(result.current.travessias.mt1[0].tipoRede).toBe('SNAP-MT1')
    // ral was not in snapshot, so it is unchanged
    expect(result.current.travessias.ral[0].tipoCabo).toBe('RAL-VALUE')
  })

  it('hasFormData is false when all fields are empty', () => {
    const { result } = renderHook(() => useFormState())
    expect(result.current.hasFormData).toBe(false)
  })

  it('hasFormData is true after any cell is filled', () => {
    const { result } = renderHook(() => useFormState())

    act(() => {
      result.current.handlers.handleTravessiaChange('ral', 0, 'tipoCabo', 'X')
    })

    expect(result.current.hasFormData).toBe(true)
  })
})

