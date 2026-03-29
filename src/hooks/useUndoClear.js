/**
 * useUndoClear — manages the APAGA (clear-all) state machine with a 5-second undo window.
 *
 * State machine:
 *   idle  →  undo_pending  →  committed  (timeout expired)
 *                          →  undone     (user clicked "Desfazer")
 *
 * Usage:
 *   const { clearState, countdown, requestClear, undoClear, commitClear } = useUndoClear({
 *     ttlMs: 5000,
 *     onCommit: () => { applyActualReset() },
 *     onUndo:   () => { restoreSnapshot() },
 *   })
 */
import { useCallback, useEffect, useRef, useState } from 'react'

const FEEDBACK_VISIBLE_MS = 2000   // How long 'committed' / 'undone' messages stay visible

/**
 * @param {object} options
 * @param {number} [options.ttlMs=5000]         Milliseconds the undo window stays open
 * @param {Function} options.onCommit            Called when the timeout fires (clear confirmed)
 * @param {Function} [options.onUndo]            Called when user undoes the clear
 * @returns {{ clearState: string, countdown: number, requestClear: Function, undoClear: Function, commitClear: Function, isUndoPending: boolean }}
 *   - `clearState`  — current state: 'idle' | 'undo_pending' | 'committed' | 'undone'
 *   - `countdown`   — seconds remaining in the undo window (0 when not in undo_pending)
 *   - `requestClear` — starts the undo countdown; call on "APAGA" button press
 *   - `undoClear`   — cancels the clear and reverts to idle
 *   - `commitClear` — immediately commits the clear without waiting for timeout
 *   - `isUndoPending` — convenience boolean; true while state === 'undo_pending'
 */
export default function useUndoClear({ ttlMs = 5000, onCommit, onUndo } = {}) {
  // 'idle' | 'undo_pending' | 'committed' | 'undone'
  const [clearState, setClearState] = useState('idle')
  const [countdown, setCountdown] = useState(0)

  const commitTimerRef   = useRef(null)
  const countdownRef     = useRef(null)
  const feedbackTimerRef = useRef(null)
  const onCommitRef      = useRef(onCommit)
  const onUndoRef        = useRef(onUndo)

  // Keep refs current so closures always call the latest versions
  useEffect(() => { onCommitRef.current = onCommit }, [onCommit])
  useEffect(() => { onUndoRef.current  = onUndo  }, [onUndo])

  const clearTimers = useCallback(() => {
    if (commitTimerRef.current)   { clearTimeout(commitTimerRef.current);   commitTimerRef.current   = null }
    if (countdownRef.current)     { clearInterval(countdownRef.current);    countdownRef.current     = null }
    if (feedbackTimerRef.current) { clearTimeout(feedbackTimerRef.current); feedbackTimerRef.current = null }
  }, [])

  // Clean up on unmount
  useEffect(() => () => clearTimers(), [clearTimers])

  /** Start the 5-second undo window */
  const requestClear = useCallback(() => {
    clearTimers()

    const totalSeconds = Math.ceil(ttlMs / 1000)
    setCountdown(totalSeconds)
    setClearState('undo_pending')

    // Tick countdown every second
    let remaining = totalSeconds
    countdownRef.current = setInterval(() => {
      remaining -= 1
      setCountdown(Math.max(0, remaining))
      if (remaining <= 0 && countdownRef.current) {
        clearInterval(countdownRef.current)
        countdownRef.current = null
      }
    }, 1000)

    // Commit after ttlMs
    commitTimerRef.current = setTimeout(() => {
      commitTimerRef.current = null
      if (countdownRef.current) { clearInterval(countdownRef.current); countdownRef.current = null }
      setClearState('committed')
      onCommitRef.current?.()
      // Return to idle after brief feedback window
      feedbackTimerRef.current = setTimeout(() => {
        setClearState('idle')
        setCountdown(0)
      }, FEEDBACK_VISIBLE_MS)
    }, ttlMs)
  }, [ttlMs, clearTimers])

  /** Cancel the undo window and restore data */
  const undoClear = useCallback(() => {
    clearTimers()
    setClearState('undone')
    setCountdown(0)
    onUndoRef.current?.()
    // Return to idle after brief feedback window
    feedbackTimerRef.current = setTimeout(() => {
      setClearState('idle')
    }, FEEDBACK_VISIBLE_MS)
  }, [clearTimers])

  /** Force-commit immediately (e.g. when navigating away mid-window) */
  const commitClear = useCallback(() => {
    clearTimers()
    setClearState('committed')
    onCommitRef.current?.()
    feedbackTimerRef.current = setTimeout(() => {
      setClearState('idle')
      setCountdown(0)
    }, FEEDBACK_VISIBLE_MS)
  }, [clearTimers])

  return {
    clearState,
    countdown,
    requestClear,
    undoClear,
    commitClear,
    isUndoPending: clearState === 'undo_pending',
  }
}
