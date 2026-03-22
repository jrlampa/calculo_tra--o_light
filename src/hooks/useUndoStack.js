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
      if (ttlTimerRef.current) clearTimeout(ttlTimerRef.current)
      
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
    if (stackRef.current.undo.length === 0) return null

    const action = stackRef.current.undo[0]
    stackRef.current.undo = stackRef.current.undo.slice(1)
    stackRef.current.redo = [action, ...stackRef.current.redo]

    setUndoStack([...stackRef.current.undo])
    setRedoStack([...stackRef.current.redo])

    return action
  }, [])

  const redo = useCallback(() => {
    if (stackRef.current.redo.length === 0) return null

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
