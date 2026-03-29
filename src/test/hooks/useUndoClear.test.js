/* Tests for the useUndoClear hook:
 * idle → undo_pending → committed (timeout)
 * idle → undo_pending → undone (user clicks Desfazer)
 * countdown, callbacks, cleanup
 */
import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

import useUndoClear from '@/hooks/useUndoClear'

// Must match FEEDBACK_VISIBLE_MS in useUndoClear.js
const FEEDBACK_VISIBLE_MS = 2000

describe('useUndoClear', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.clearAllMocks()
  })

  // ─── initial state ──────────────────────────────────────────────────────────
  it('starts in idle state with countdown 0', () => {
    const { result } = renderHook(() => useUndoClear({ ttlMs: 5000, onCommit: () => {} }))
    expect(result.current.clearState).toBe('idle')
    expect(result.current.countdown).toBe(0)
    expect(result.current.isUndoPending).toBe(false)
  })

  // ─── requestClear ───────────────────────────────────────────────────────────
  it('requestClear transitions to undo_pending with full countdown', () => {
    const { result } = renderHook(() => useUndoClear({ ttlMs: 5000, onCommit: () => {} }))

    act(() => { result.current.requestClear() })

    expect(result.current.clearState).toBe('undo_pending')
    expect(result.current.countdown).toBe(5)
    expect(result.current.isUndoPending).toBe(true)
  })

  it('countdown decrements every second', () => {
    const { result } = renderHook(() => useUndoClear({ ttlMs: 5000, onCommit: () => {} }))

    act(() => { result.current.requestClear() })
    act(() => { vi.advanceTimersByTime(1000) })
    expect(result.current.countdown).toBe(4)

    act(() => { vi.advanceTimersByTime(1000) })
    expect(result.current.countdown).toBe(3)
  })

  // ─── committed path (timeout) ───────────────────────────────────────────────
  it('transitions to committed and calls onCommit after ttlMs', () => {
    const onCommit = vi.fn()
    const { result } = renderHook(() => useUndoClear({ ttlMs: 5000, onCommit }))

    act(() => { result.current.requestClear() })
    act(() => { vi.advanceTimersByTime(5000) })

    expect(result.current.clearState).toBe('committed')
    expect(onCommit).toHaveBeenCalledTimes(1)
  })

  it('returns to idle after brief feedback window following commit', () => {
    const onCommit = vi.fn()
    const { result } = renderHook(() => useUndoClear({ ttlMs: 5000, onCommit }))

    act(() => { result.current.requestClear() })
    act(() => { vi.advanceTimersByTime(5000 + FEEDBACK_VISIBLE_MS) })

    expect(result.current.clearState).toBe('idle')
    expect(result.current.countdown).toBe(0)
  })

  // ─── undone path ────────────────────────────────────────────────────────────
  it('undoClear transitions to undone and calls onUndo', () => {
    const onUndo = vi.fn()
    const { result } = renderHook(() =>
      useUndoClear({ ttlMs: 5000, onCommit: () => {}, onUndo })
    )

    act(() => { result.current.requestClear() })
    act(() => { result.current.undoClear() })

    expect(result.current.clearState).toBe('undone')
    expect(onUndo).toHaveBeenCalledTimes(1)
  })

  it('undoClear cancels the pending commit timer (onCommit not called)', () => {
    const onCommit = vi.fn()
    const { result } = renderHook(() => useUndoClear({ ttlMs: 5000, onCommit }))

    act(() => { result.current.requestClear() })
    act(() => { result.current.undoClear() })
    // Advance past the original timeout
    act(() => { vi.advanceTimersByTime(5000) })

    expect(onCommit).not.toHaveBeenCalled()
  })

  it('returns to idle after feedback window following undo', () => {
    const { result } = renderHook(() =>
      useUndoClear({ ttlMs: 5000, onCommit: () => {}, onUndo: () => {} })
    )

    act(() => { result.current.requestClear() })
    act(() => { result.current.undoClear() })
    act(() => { vi.advanceTimersByTime(FEEDBACK_VISIBLE_MS) })

    expect(result.current.clearState).toBe('idle')
  })

  // ─── re-trigger requestClear ────────────────────────────────────────────────
  it('calling requestClear again resets the countdown from the top', () => {
    const onCommit = vi.fn()
    const { result } = renderHook(() => useUndoClear({ ttlMs: 5000, onCommit }))

    act(() => { result.current.requestClear() })
    act(() => { vi.advanceTimersByTime(3000) })   // Advance 3 s
    expect(result.current.countdown).toBe(2)

    // Trigger again — countdown should restart at 5
    act(() => { result.current.requestClear() })
    expect(result.current.countdown).toBe(5)

    // Old timer cancelled — advance another 2 s (only 2 s into new 5 s window)
    act(() => { vi.advanceTimersByTime(2000) })
    expect(onCommit).not.toHaveBeenCalled()
  })

  // ─── onCommit / onUndo ref stability ────────────────────────────────────────
  it('always calls the latest onCommit even if callback identity changes', () => {
    const onCommit1 = vi.fn()
    const onCommit2 = vi.fn()

    const { result, rerender } = renderHook(
      ({ cb }) => useUndoClear({ ttlMs: 5000, onCommit: cb }),
      { initialProps: { cb: onCommit1 } }
    )

    act(() => { result.current.requestClear() })
    rerender({ cb: onCommit2 })   // Swap callback mid-window
    act(() => { vi.advanceTimersByTime(5000) })

    expect(onCommit1).not.toHaveBeenCalled()
    expect(onCommit2).toHaveBeenCalledTimes(1)
  })

  // ─── custom ttlMs ───────────────────────────────────────────────────────────
  it('respects a custom ttlMs (3 s)', () => {
    const onCommit = vi.fn()
    const { result } = renderHook(() => useUndoClear({ ttlMs: 3000, onCommit }))

    act(() => { result.current.requestClear() })
    expect(result.current.countdown).toBe(3)

    act(() => { vi.advanceTimersByTime(3000) })
    expect(onCommit).toHaveBeenCalledTimes(1)
  })
})
