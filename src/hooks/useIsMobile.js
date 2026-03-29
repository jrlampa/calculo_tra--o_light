/**
 * useIsMobile.js — React hook that returns `true` when the viewport width is
 * ≤ the given breakpoint (default 767 px, matching the mobile breakpoint used
 * throughout the application's CSS).
 *
 * Listens to the `change` event of the MediaQueryList so the value updates
 * without a full page reload when the viewport is resized (e.g. DevTools or
 * orientation change on a physical device).
 *
 * @param {number} [breakpoint=767] - Max-width threshold in pixels (inclusive).
 * @returns {boolean} `true` when viewport width ≤ breakpoint.
 */
import { useState, useEffect } from 'react'

export function useIsMobile(breakpoint = 767) {
  const query = `(max-width: ${breakpoint}px)`

  const [isMobile, setIsMobile] = useState(() => {
    if (typeof window === 'undefined') { return false }
    return window.matchMedia(query).matches
  })

  useEffect(() => {
    if (typeof window === 'undefined') { return undefined }

    const mql = window.matchMedia(query)
    const onChange = (e) => { setIsMobile(e.matches) }

    // Use addEventListener when available (modern browsers), fall back to the
    // deprecated addListener for legacy Safari < 14.
    if (typeof mql.addEventListener === 'function') {
      mql.addEventListener('change', onChange)
    } else {
      mql.addListener(onChange)
    }

    // Sync on mount in case the initial SSR guess was wrong.
    setIsMobile(mql.matches)

    return () => {
      if (typeof mql.removeEventListener === 'function') {
        mql.removeEventListener('change', onChange)
      } else {
        mql.removeListener(onChange)
      }
    }
  }, [query])

  return isMobile
}
