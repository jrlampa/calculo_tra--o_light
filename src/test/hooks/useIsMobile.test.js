/* Tests for the useIsMobile hook.
 *
 * The window.matchMedia mock is defined in src/test/setup.js and always
 * returns { matches: false }.  Here we override it per-test to simulate
 * different viewport states and to exercise the change-event listener.
 */
import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, beforeEach, vi } from 'vitest'

import { useIsMobile } from '@/hooks/useIsMobile'

function makeMql(initialMatches = false) {
  const listeners = []
  const mql = {
    matches: initialMatches,
    media: '',
    onchange: null,
    addEventListener: vi.fn((event, handler) => {
      if (event === 'change') { listeners.push(handler) }
    }),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
    // helper used by tests to simulate a resize
    _fire: (matches) => {
      mql.matches = matches
      listeners.forEach((fn) => fn({ matches }))
    },
  }
  return mql
}

describe('useIsMobile', () => {
  let mql

  beforeEach(() => {
    mql = makeMql(false)
    vi.spyOn(window, 'matchMedia').mockReturnValue(mql)
  })

  it('returns false when viewport is wider than default breakpoint', () => {
    mql.matches = false
    const { result } = renderHook(() => useIsMobile())
    expect(result.current).toBe(false)
  })

  it('returns true when matchMedia already matches on mount (narrow viewport)', () => {
    mql = makeMql(true)
    window.matchMedia.mockReturnValue(mql)
    const { result } = renderHook(() => useIsMobile())
    expect(result.current).toBe(true)
  })

  it('updates from false to true when viewport shrinks below breakpoint', () => {
    const { result } = renderHook(() => useIsMobile())
    expect(result.current).toBe(false)

    act(() => { mql._fire(true) })
    expect(result.current).toBe(true)
  })

  it('updates from true to false when viewport expands above breakpoint', () => {
    mql = makeMql(true)
    window.matchMedia.mockReturnValue(mql)
    const { result } = renderHook(() => useIsMobile())
    expect(result.current).toBe(true)

    act(() => { mql._fire(false) })
    expect(result.current).toBe(false)
  })

  it('uses the provided breakpoint to build the media query', () => {
    renderHook(() => useIsMobile(480))
    expect(window.matchMedia).toHaveBeenCalledWith('(max-width: 480px)')
  })

  it('uses 767px as the default breakpoint', () => {
    renderHook(() => useIsMobile())
    expect(window.matchMedia).toHaveBeenCalledWith('(max-width: 767px)')
  })

  it('attaches a change event listener on mount', () => {
    renderHook(() => useIsMobile())
    expect(mql.addEventListener).toHaveBeenCalledWith('change', expect.any(Function))
  })

  it('removes the change event listener on unmount', () => {
    const { unmount } = renderHook(() => useIsMobile())

    // Capture the exact handler reference that was registered
    const registeredHandler = mql.addEventListener.mock.calls[0]?.[1]
    expect(registeredHandler).toBeTypeOf('function')

    unmount()

    // removeEventListener must be called with the identical handler reference
    expect(mql.removeEventListener).toHaveBeenCalledWith('change', registeredHandler)
  })

  it('falls back to addListener when addEventListener is not a function', () => {
    const legacyMql = {
      matches: false,
      media: '',
      addListener: vi.fn(),
      removeListener: vi.fn(),
    }
    window.matchMedia.mockReturnValue(legacyMql)
    const { unmount } = renderHook(() => useIsMobile())
    expect(legacyMql.addListener).toHaveBeenCalled()
    unmount()
    expect(legacyMql.removeListener).toHaveBeenCalled()
  })
})
