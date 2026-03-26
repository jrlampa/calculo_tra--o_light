/* Tests for the useValidation and useTravessiaValidation hooks */
import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useValidation, useTravessiaValidation } from '@/hooks/useValidation'

// ─── useValidation ────────────────────────────────────────────────────────────
describe('useValidation', () => {
  const rules = {
    nome: { required: 'Nome é obrigatório' },
    vao: {
      min: 0,
      max: 1000,
    },
    codigo: {
      pattern: { test: (v) => /^[A-Z]{2}-\d{3}$/.test(v), message: 'Formato inválido' },
    },
  }

  it('initialises with provided values', () => {
    const { result } = renderHook(() =>
      useValidation({ nome: 'Teste', vao: '50' }, rules)
    )
    expect(result.current.values.nome).toBe('Teste')
    expect(result.current.values.vao).toBe('50')
  })

  it('isValid is true when there are no errors', () => {
    const { result } = renderHook(() => useValidation({}, rules))
    expect(result.current.isValid).toBe(true)
  })

  it('isDirty is false for initial values', () => {
    const { result } = renderHook(() => useValidation({ nome: '' }, rules))
    expect(result.current.isDirty).toBe(false)
  })

  it('isDirty is true after setValue changes a field', () => {
    const { result } = renderHook(() => useValidation({ nome: '' }, rules))
    act(() => { result.current.setValue('nome', 'Novo') })
    expect(result.current.isDirty).toBe(true)
  })

  it('validate returns false and sets error for missing required field', () => {
    const { result } = renderHook(() =>
      useValidation({ nome: '' }, rules)
    )
    let valid
    act(() => { valid = result.current.validate() })
    expect(valid).toBe(false)
    expect(result.current.errors.nome).toBe('Nome é obrigatório')
  })

  it('validate returns true when all required fields are filled', () => {
    const { result } = renderHook(() =>
      useValidation({ nome: 'João', vao: '50', codigo: 'AB-123' }, rules)
    )
    let valid
    act(() => { valid = result.current.validate() })
    expect(valid).toBe(true)
  })

  it('validate catches min / max violations', () => {
    const { result } = renderHook(() =>
      useValidation({ nome: 'OK', vao: '1500', codigo: '' }, rules)
    )
    let valid
    act(() => { valid = result.current.validate() })
    expect(valid).toBe(false)
    expect(result.current.errors.vao).toMatch(/Valor máximo/)
  })

  it('validate catches pattern violations', () => {
    const { result } = renderHook(() =>
      useValidation({ nome: 'OK', vao: '50', codigo: 'bad' }, rules)
    )
    let valid
    act(() => { valid = result.current.validate() })
    expect(valid).toBe(false)
    expect(result.current.errors.codigo).toBe('Formato inválido')
  })

  it('validateField updates only the specified field error', () => {
    const { result } = renderHook(() =>
      useValidation({ nome: '', vao: '50' }, rules)
    )
    let fieldValid
    act(() => { fieldValid = result.current.validateField('nome', '') })
    expect(fieldValid).toBe(false)
    expect(result.current.errors.nome).toBe('Nome é obrigatório')
    // other fields untouched
    expect(result.current.errors.vao).toBeUndefined()
  })

  it('setFieldTouched marks field as touched and validates it', () => {
    const { result } = renderHook(() =>
      useValidation({ nome: '' }, rules)
    )
    act(() => { result.current.setFieldTouched('nome') })
    expect(result.current.touched.nome).toBe(true)
    expect(result.current.errors.nome).toBe('Nome é obrigatório')
  })

  it('setValue re-validates touched field on change', () => {
    const { result } = renderHook(() =>
      useValidation({ nome: '' }, rules)
    )
    // touch and trigger error
    act(() => { result.current.setFieldTouched('nome') })
    expect(result.current.errors.nome).toBeTruthy()

    // fix the value — error should clear
    act(() => { result.current.setValue('nome', 'João') })
    expect(result.current.errors.nome).toBeNull()
  })

  it('setAllTouched marks every rule-field as touched', () => {
    const { result } = renderHook(() =>
      useValidation({ nome: '', vao: '50', codigo: '' }, rules)
    )
    act(() => { result.current.setAllTouched() })
    expect(result.current.touched.nome).toBe(true)
    expect(result.current.touched.vao).toBe(true)
    expect(result.current.touched.codigo).toBe(true)
  })

  it('resetValidation clears errors and touched state', () => {
    const { result } = renderHook(() =>
      useValidation({ nome: '' }, rules)
    )
    act(() => { result.current.setAllTouched() })
    act(() => { result.current.resetValidation() })
    expect(result.current.errors).toEqual({})
    expect(result.current.touched).toEqual({})
  })
})

// ─── useTravessiaValidation ───────────────────────────────────────────────────
describe('useTravessiaValidation', () => {
  const travessias = [
    { vao: '50', flecha: '1.2', angulo: '10', tipoRede: 'MT', tipoCabo: 'CAA 120' },
    { vao: '60', flecha: '1.5', angulo: '20', tipoRede: 'BT', tipoCabo: 'CAA 50' },
  ]

  it('starts with no errors', () => {
    const { result } = renderHook(() => useTravessiaValidation(travessias))
    expect(result.current.hasErrors).toBe(false)
  })

  it('validateTravessia accepts valid numeric inputs', () => {
    const { result } = renderHook(() => useTravessiaValidation(travessias))
    let ok
    act(() => { ok = result.current.validateTravessia(0, 'vao', '80') })
    expect(ok).toBe(true)
    expect(result.current.getError(0, 'vao')).toBeNull()
  })

  it('validateTravessia rejects non-numeric vao', () => {
    const { result } = renderHook(() => useTravessiaValidation(travessias))
    let ok
    act(() => { ok = result.current.validateTravessia(0, 'vao', 'abc') })
    expect(ok).toBe(false)
    expect(result.current.getError(0, 'vao')).toBeTruthy()
  })

  it('validateTravessia rejects negative vao', () => {
    const { result } = renderHook(() => useTravessiaValidation(travessias))
    let ok
    act(() => { ok = result.current.validateTravessia(0, 'vao', '-5') })
    expect(ok).toBe(false)
  })

  it('validateTravessia rejects vao > 1000', () => {
    const { result } = renderHook(() => useTravessiaValidation(travessias))
    let ok
    act(() => { ok = result.current.validateTravessia(0, 'vao', '1001') })
    expect(ok).toBe(false)
  })

  it('validateTravessia rejects flecha > 50', () => {
    const { result } = renderHook(() => useTravessiaValidation(travessias))
    let ok
    act(() => { ok = result.current.validateTravessia(0, 'flecha', '51') })
    expect(ok).toBe(false)
  })

  it('validateTravessia rejects angulo > 360', () => {
    const { result } = renderHook(() => useTravessiaValidation(travessias))
    let ok
    act(() => { ok = result.current.validateTravessia(0, 'angulo', '361') })
    expect(ok).toBe(false)
  })

  it('validateTravessia rejects tipoRede longer than 50 chars', () => {
    const { result } = renderHook(() => useTravessiaValidation(travessias))
    let ok
    act(() => { ok = result.current.validateTravessia(0, 'tipoRede', 'A'.repeat(51)) })
    expect(ok).toBe(false)
  })

  it('validateAllTravessias returns true for all-valid travessias', () => {
    const { result } = renderHook(() => useTravessiaValidation(travessias))
    let ok
    act(() => { ok = result.current.validateAllTravessias() })
    expect(ok).toBe(true)
    expect(result.current.hasErrors).toBe(false)
  })

  it('validateAllTravessias returns false and records errors when data is invalid', () => {
    const bad = [
      { vao: '-1', flecha: '1', angulo: '10', tipoRede: 'MT', tipoCabo: 'CAA' },
    ]
    const { result } = renderHook(() => useTravessiaValidation(bad))
    let ok
    act(() => { ok = result.current.validateAllTravessias() })
    expect(ok).toBe(false)
    expect(result.current.hasErrors).toBe(true)
  })

  it('clearErrors removes all recorded errors', () => {
    const bad = [{ vao: '-1', flecha: '1', angulo: '10', tipoRede: 'MT', tipoCabo: 'OK' }]
    const { result } = renderHook(() => useTravessiaValidation(bad))
    act(() => { result.current.validateAllTravessias() })
    act(() => { result.current.clearErrors() })
    expect(result.current.hasErrors).toBe(false)
    expect(result.current.errors).toEqual({})
  })
})
