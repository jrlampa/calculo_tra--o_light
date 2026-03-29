/**
 * The `useUndoStack` custom hook in JavaScript manages undo and redo functionality with expiration
 * based on a specified time-to-live (TTL) for actions.
 * @param pontoId - The `pontoId` parameter in the `useUndoStack` hook is used to identify the specific
 * instance of the hook. When the `pontoId` changes, the hook will reset its state, clearing the undo
 * and redo stacks. This can be useful when you have multiple instances of the
 * @param [maxSize] - The `maxSize` parameter in the `useUndoStack` hook determines the maximum number
 * of actions that can be stored in the undo stack. When a new action is pushed onto the stack and the
 * size exceeds `maxSize`, the oldest action is removed to maintain the limit.
 * @param [ttlMs] - The `ttlMs` parameter in the `useUndoStack` hook stands for "time to live in
 * milliseconds". It determines the duration for which the undo actions are kept in the stack before
 * they expire and are cleared. In this case, the default `ttlMs` value is set to 5
 * @returns The `useUndoStack` custom hook returns an object with the following properties and
 * functions:
 */
import { useCallback, useEffect, useRef, useState } from 'react'

import { trackUxFunnelEvent, UX_FUNNEL_EVENTS } from '../services/uxFunnelInstrumentation.js'

const DEFAULT_MAX_SIZE = 10
const DEFAULT_TTL_MS = 5 * 60 * 1000 // 5 minutes

export default function useUndoStack(pontoId, maxSize = DEFAULT_MAX_SIZE, ttlMs = DEFAULT_TTL_MS) {
  const [undoStack, setUndoStack] = useState([])
  const [redoStack, setRedoStack] = useState([])
  
  const stackRef = useRef({ undo: [], redo: [], expiresAt: null })
  const ttlTimerRef = useRef(null)

  useEffect(() => {
    setUndoStack([])
    setRedoStack([])
    stackRef.current = { undo: [], redo: [], expiresAt: null }
    
    if (ttlTimerRef.current) {
      clearTimeout(ttlTimerRef.current)
      ttlTimerRef.current = null
    }
  }, [pontoId])

  useEffect(() => {
    if (undoStack.length > 0) {
      if (ttlTimerRef.current) {clearTimeout(ttlTimerRef.current)}
      
      ttlTimerRef.current = setTimeout(() => {
        const expiredCount = stackRef.current.undo.length
        setUndoStack([])
        setRedoStack([])
        stackRef.current = { undo: [], redo: [], expiresAt: null }
        ttlTimerRef.current = null
        trackUxFunnelEvent(UX_FUNNEL_EVENTS.UNDO_EXPIRED, {
          expired_actions_count: expiredCount,
        })
      }, ttlMs)
    }

    return () => {
      if (ttlTimerRef.current) {
        clearTimeout(ttlTimerRef.current)
        ttlTimerRef.current = null
      }
    }
  }, [undoStack.length, ttlMs])

  const push = useCallback((fieldKey, oldValue, newValue) => {
    const action = {
      timestamp: Date.now(),
      fieldKey,
      oldValue,
      newValue,
    }

    const newUndoStack = [action, ...stackRef.current.undo].slice(0, maxSize)
    
    stackRef.current.undo = newUndoStack
    stackRef.current.redo = []
    stackRef.current.expiresAt = Date.now() + ttlMs

    setUndoStack(newUndoStack)
    setRedoStack([])
  }, [maxSize, ttlMs])

  const undo = useCallback(() => {
    if (stackRef.current.undo.length === 0) {return null}

    const action = stackRef.current.undo[0]
    stackRef.current.undo = stackRef.current.undo.slice(1)
    stackRef.current.redo = [action, ...stackRef.current.redo]

    setUndoStack([...stackRef.current.undo])
    setRedoStack([...stackRef.current.redo])

    return action
  }, [])

  const redo = useCallback(() => {
    if (stackRef.current.redo.length === 0) {return null}

    const action = stackRef.current.redo[0]
    stackRef.current.redo = stackRef.current.redo.slice(1)
    stackRef.current.undo = [action, ...stackRef.current.undo]

    setUndoStack([...stackRef.current.undo])
    setRedoStack([...stackRef.current.redo])

    return action
  }, [])

  const clear = useCallback(() => {
    stackRef.current = { undo: [], redo: [], expiresAt: null }
    setUndoStack([])
    setRedoStack([])
  }, [])

  const isExpired = Date.now() > (stackRef.current.expiresAt || 0)
  const canUndo = undoStack.length > 0 && !isExpired
  const canRedo = redoStack.length > 0 && !isExpired

  return {
    undoStack,
    redoStack,
    push,
    undo,
    redo,
    canUndo,
    canRedo,
    isExpired,
    clear,
  }
}
