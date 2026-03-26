/* Tests for the useUndoStack custom hook:
 * push, undo, redo, clear, maxSize cap, canUndo / canRedo, TTL expiry
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import useUndoStack from '@/hooks/useUndoStack'

describe('useUndoStack', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  // ─── initial state ──────────────────────────────────────────────────────────
  it('starts with empty stacks', () => {
    const { result } = renderHook(() => useUndoStack('ponto-1'))
    expect(result.current.undoStack).toHaveLength(0)
    expect(result.current.redoStack).toHaveLength(0)
    expect(result.current.canUndo).toBe(false)
    expect(result.current.canRedo).toBe(false)
  })

  // ─── push ───────────────────────────────────────────────────────────────────
  it('push adds an action to the undo stack', () => {
    const { result } = renderHook(() => useUndoStack('ponto-1'))

    act(() => {
      result.current.push('vao', '50', '60')
    })

    expect(result.current.undoStack).toHaveLength(1)
    expect(result.current.undoStack[0]).toMatchObject({ fieldKey: 'vao', oldValue: '50', newValue: '60' })
    expect(result.current.canUndo).toBe(true)
  })

  it('push clears the redo stack', () => {
    const { result } = renderHook(() => useUndoStack('ponto-1'))

    act(() => { result.current.push('vao', '50', '60') })
    act(() => { result.current.undo() })

    expect(result.current.canRedo).toBe(true)

    act(() => { result.current.push('flecha', '1', '2') })

    expect(result.current.redoStack).toHaveLength(0)
    expect(result.current.canRedo).toBe(false)
  })

  it('most-recent action is at index 0', () => {
    const { result } = renderHook(() => useUndoStack('ponto-1'))

    act(() => { result.current.push('vao', '50', '60') })
    act(() => { result.current.push('flecha', '1', '2') })

    expect(result.current.undoStack[0].fieldKey).toBe('flecha')
    expect(result.current.undoStack[1].fieldKey).toBe('vao')
  })

  // ─── maxSize cap ────────────────────────────────────────────────────────────
  it('caps the undo stack at maxSize', () => {
    const { result } = renderHook(() => useUndoStack('ponto-1', 3))

    act(() => { result.current.push('a', 0, 1) })
    act(() => { result.current.push('b', 0, 1) })
    act(() => { result.current.push('c', 0, 1) })
    act(() => { result.current.push('d', 0, 1) }) // should drop oldest

    expect(result.current.undoStack).toHaveLength(3)
    expect(result.current.undoStack[0].fieldKey).toBe('d')
    expect(result.current.undoStack[2].fieldKey).toBe('b') // oldest remaining
  })

  // ─── undo ───────────────────────────────────────────────────────────────────
  it('undo removes the top action from undoStack and moves it to redoStack', () => {
    const { result } = renderHook(() => useUndoStack('ponto-1'))

    act(() => { result.current.push('vao', '50', '60') })
    let action
    act(() => { action = result.current.undo() })

    expect(action).toMatchObject({ fieldKey: 'vao', oldValue: '50', newValue: '60' })
    expect(result.current.undoStack).toHaveLength(0)
    expect(result.current.redoStack).toHaveLength(1)
    expect(result.current.canUndo).toBe(false)
    expect(result.current.canRedo).toBe(true)
  })

  it('undo returns null when stack is empty', () => {
    const { result } = renderHook(() => useUndoStack('ponto-1'))
    let action
    act(() => { action = result.current.undo() })
    expect(action).toBeNull()
  })

  // ─── redo ───────────────────────────────────────────────────────────────────
  it('redo moves the top redo action back to undoStack', () => {
    const { result } = renderHook(() => useUndoStack('ponto-1'))

    act(() => { result.current.push('vao', '50', '60') })
    act(() => { result.current.undo() })
    let action
    act(() => { action = result.current.redo() })

    expect(action).toMatchObject({ fieldKey: 'vao', oldValue: '50', newValue: '60' })
    expect(result.current.undoStack).toHaveLength(1)
    expect(result.current.redoStack).toHaveLength(0)
    expect(result.current.canRedo).toBe(false)
    expect(result.current.canUndo).toBe(true)
  })

  it('redo returns null when redo stack is empty', () => {
    const { result } = renderHook(() => useUndoStack('ponto-1'))
    let action
    act(() => { action = result.current.redo() })
    expect(action).toBeNull()
  })

  // ─── clear ──────────────────────────────────────────────────────────────────
  it('clear empties both stacks', () => {
    const { result } = renderHook(() => useUndoStack('ponto-1'))

    act(() => { result.current.push('vao', '50', '60') })
    act(() => { result.current.push('flecha', '1', '2') })
    act(() => { result.current.clear() })

    expect(result.current.undoStack).toHaveLength(0)
    expect(result.current.redoStack).toHaveLength(0)
    expect(result.current.canUndo).toBe(false)
    expect(result.current.canRedo).toBe(false)
  })

  // ─── pontoId change resets state ────────────────────────────────────────────
  it('resets both stacks when pontoId changes', () => {
    const { result, rerender } = renderHook(
      ({ id }) => useUndoStack(id),
      { initialProps: { id: 'ponto-1' } }
    )

    act(() => { result.current.push('vao', '50', '60') })
    expect(result.current.undoStack).toHaveLength(1)

    rerender({ id: 'ponto-2' })

    expect(result.current.undoStack).toHaveLength(0)
    expect(result.current.canUndo).toBe(false)
  })

  // ─── TTL expiry ─────────────────────────────────────────────────────────────
  it('canUndo becomes false after TTL expires', () => {
    const ttl = 5000
    const { result } = renderHook(() => useUndoStack('ponto-1', 10, ttl))

    act(() => { result.current.push('vao', '50', '60') })
    expect(result.current.canUndo).toBe(true)

    act(() => { vi.advanceTimersByTime(ttl + 100) })

    // After TTL the stacks are cleared
    expect(result.current.undoStack).toHaveLength(0)
    expect(result.current.canUndo).toBe(false)
  })

  // ─── timestamp on push ──────────────────────────────────────────────────────
  it('each pushed action carries a numeric timestamp', () => {
    const { result } = renderHook(() => useUndoStack('ponto-1'))
    act(() => { result.current.push('vao', '50', '60') })
    expect(typeof result.current.undoStack[0].timestamp).toBe('number')
  })
})
