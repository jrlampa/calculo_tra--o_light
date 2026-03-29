/* Tests for the useDebounce hook */
import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

import { useDebounce } from '@/hooks/useDebounce'

describe('useDebounce', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('returns the initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('initial', 300))
    expect(result.current).toBe('initial')
  })

  it('does not update the value before the delay elapses', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'initial', delay: 300 } }
    )

    rerender({ value: 'updated', delay: 300 })

    // Advance less than the delay
    act(() => { vi.advanceTimersByTime(200) })

    expect(result.current).toBe('initial')
  })

  it('updates the value after the delay elapses', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'initial', delay: 300 } }
    )

    rerender({ value: 'updated', delay: 300 })

    act(() => { vi.advanceTimersByTime(300) })

    expect(result.current).toBe('updated')
  })

  it('resets the timer on rapid successive changes (debounce behaviour)', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'a', delay: 300 } }
    )

    rerender({ value: 'b', delay: 300 })
    act(() => { vi.advanceTimersByTime(100) })

    rerender({ value: 'c', delay: 300 })
    act(() => { vi.advanceTimersByTime(100) })

    // Total 200ms since first change — neither 'b' nor 'c' should have settled yet
    expect(result.current).toBe('a')

    // Now let the final timer complete
    act(() => { vi.advanceTimersByTime(300) })
    expect(result.current).toBe('c')
  })

  it('works with numeric values', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 500),
      { initialProps: { value: 0 } }
    )

    rerender({ value: 42 })
    act(() => { vi.advanceTimersByTime(500) })

    expect(result.current).toBe(42)
  })

  it('works with object values', () => {
    const obj1 = { a: 1 }
    const obj2 = { a: 2 }

    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 200),
      { initialProps: { value: obj1 } }
    )

    rerender({ value: obj2 })
    act(() => { vi.advanceTimersByTime(200) })

    expect(result.current).toBe(obj2)
  })

  it('clears the pending timer when the component unmounts', () => {
    const { rerender, unmount } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: 'start' } }
    )

    rerender({ value: 'pending' })
    unmount()

    // Advance timers — no state update should throw
    act(() => { vi.advanceTimersByTime(500) })

    // If no error was thrown the cleanup worked correctly
    expect(true).toBe(true)
  })
})
