/**
 * The `usePersistenciaCalculo` custom hook manages the persistence of calculation data with retry
 * logic and error handling.
 * @returns The `usePersistenciaCalculo` custom hook is returning an object with three properties:
 */
import { useCallback, useEffect, useRef, useState } from 'react'
import {
  buildSalvarCalculoPayload,
  getLastRequestContext,
  persistCalculo,
} from '../services/calculoApi.js'
import { trackUxFunnelEvent, UX_FUNNEL_EVENTS } from '../services/uxFunnelInstrumentation.js'

const PERSIST_WINDOW_MS = 5000
const MAX_RETRIES = 3

export default function usePersistenciaCalculo({ pontoId, lastPayload, resultado, autoSave = true }) {
  const [persistencia, setPersistencia] = useState({ 
    status: 'idle', 
    error: '', 
    willRetry: false,
    canRetry: false,
    isForbidden: false,
    retryInSeconds: 0
  })
  const lastPersistSignatureRef = useRef('')
  const lastPersistAtRef = useRef(0)
  const persistTimerRef = useRef(null)
  const persistInFlightRef = useRef(false)
  const pendingPersistRef = useRef(null)
  const retryCountRef = useRef(0)
  const retryCountdownRef = useRef(null)

  const clearPersistTimer = useCallback(() => {
    if (persistTimerRef.current) {
      clearTimeout(persistTimerRef.current)
      persistTimerRef.current = null
    }
    if (retryCountdownRef.current) {
      clearInterval(retryCountdownRef.current)
      retryCountdownRef.current = null
    }
  }, [])

  // Inicia countdown de segundos para retry
  const startRetryCountdown = useCallback((backoffMs) => {
    if (retryCountdownRef.current) clearInterval(retryCountdownRef.current)
    
    let secondsRemaining = Math.ceil(backoffMs / 1000)
    
    setPersistencia(prevState => ({
      ...prevState,
      retryInSeconds: secondsRemaining,
      willRetry: true
    }))

    retryCountdownRef.current = setInterval(() => {
      secondsRemaining -= 1
      setPersistencia(prevState => ({
        ...prevState,
        retryInSeconds: Math.max(0, secondsRemaining)
      }))
      
      if (secondsRemaining <= 0 && retryCountdownRef.current) {
        clearInterval(retryCountdownRef.current)
        retryCountdownRef.current = null
      }
    }, 1000)
  }, [])

  const flushPersistQueue = useCallback(async () => {
    if (persistInFlightRef.current) return

    const nextPersist = pendingPersistRef.current
    if (!nextPersist) return

    clearPersistTimer()
    persistInFlightRef.current = true
    setPersistencia(prevState => ({ 
      ...prevState, 
      status: 'saving', 
      error: '',
      willRetry: false,
      isForbidden: false
    }))

    try {
      await persistCalculo(nextPersist.pontoId, nextPersist.payload)
      const { operation_id: operationId } = getLastRequestContext()
      // Sucesso confirmado — limpa o pending somente se ainda for o mesmo item
      if (pendingPersistRef.current === nextPersist) {
        pendingPersistRef.current = null
      }
      retryCountRef.current = 0
      lastPersistSignatureRef.current = nextPersist.signature
      lastPersistAtRef.current = Date.now()
      setPersistencia(prevState => ({
        ...prevState,
        status: pendingPersistRef.current ? 'queued' : 'saved',
        error: '',
        willRetry: false,
        isForbidden: false
      }))
      trackUxFunnelEvent(UX_FUNNEL_EVENTS.PERSISTENCE_SAVED, {
        ponto_id: nextPersist.pontoId,
        operation_id: operationId || null,
        has_queue: Boolean(pendingPersistRef.current),
      })
      trackUxFunnelEvent(UX_FUNNEL_EVENTS.CALCULATION_PERSISTED, {
        ponto_id: nextPersist.pontoId,
        operation_id: operationId || null,
      })
    } catch (err) {
      // Detectar erro de autorização (403, FORBIDDEN, permission denied)
      const isForbidden = err.status === 403 || err.isForbidden || err.code === 'FORBIDDEN'
      
      if (isForbidden) {
        // Erro de autorização: NÃO retentar automaticamente
        setPersistencia(prevState => ({
          ...prevState,
          status: 'error',
          error: err.message || 'Acesso negado',
          willRetry: false,
          canRetry: true,  // Permitir retry manual depois de reconfirmar ponto
          isForbidden: true,
          retryInSeconds: 0
        }))
        retryCountRef.current = 0
        trackUxFunnelEvent(UX_FUNNEL_EVENTS.PERSISTENCE_FAILED, {
          ponto_id: nextPersist.pontoId,
          operation_id: err.operationId || null,
          is_forbidden: true,
          will_retry: false,
          error: err.message || 'Acesso negado',
        })
      } else {
        // Erro transiente: tentar retentar automaticamente
        retryCountRef.current += 1
        if (retryCountRef.current <= MAX_RETRIES) {
          const backoffMs = Math.min(1000 * 2 ** retryCountRef.current, 30_000)
          startRetryCountdown(backoffMs)
          setPersistencia(prevState => ({
            ...prevState,
            status: 'error',
            error: err.message,
            willRetry: true,
            canRetry: false,
            isForbidden: false
          }))
          clearPersistTimer()
          persistTimerRef.current = setTimeout(() => void flushPersistQueue(), backoffMs)
          trackUxFunnelEvent(UX_FUNNEL_EVENTS.PERSISTENCE_FAILED, {
            ponto_id: nextPersist.pontoId,
            operation_id: err.operationId || null,
            is_forbidden: false,
            will_retry: true,
            retry_count: retryCountRef.current,
            error: err.message || 'Erro ao persistir cálculo',
          })
        } else {
          // Esgotadas as tentativas
          retryCountRef.current = 0
          setPersistencia(prevState => ({
            ...prevState,
            status: 'error',
            error: err.message,
            willRetry: false,
            canRetry: true,
            isForbidden: false,
            retryInSeconds: 0
          }))
          trackUxFunnelEvent(UX_FUNNEL_EVENTS.PERSISTENCE_FAILED, {
            ponto_id: nextPersist.pontoId,
            operation_id: err.operationId || null,
            is_forbidden: false,
            will_retry: false,
            retry_count: MAX_RETRIES,
            error: err.message || 'Erro ao persistir cálculo',
          })
        }
      }
    } finally {
      persistInFlightRef.current = false

      if (!pendingPersistRef.current) return

      const elapsedMs = Date.now() - lastPersistAtRef.current
      const waitMs = Math.max(PERSIST_WINDOW_MS - elapsedMs, 0)

      if (waitMs > 0) {
        setPersistencia(prevState => ({ 
          ...prevState, 
          status: 'queued', 
          error: '',
          willRetry: false
        }))
        clearPersistTimer()
        persistTimerRef.current = setTimeout(() => {
          void flushPersistQueue()
        }, waitMs)
        return
      }

      void flushPersistQueue()
    }
  }, [clearPersistTimer, startRetryCountdown])

  const schedulePersistQueue = useCallback(() => {
    if (!pendingPersistRef.current) return

    if (persistInFlightRef.current) {
      setPersistencia(prevState => ({ 
        ...prevState, 
        status: 'queued', 
        error: '',
        willRetry: false
      }))
      return
    }

    const elapsedMs = Date.now() - lastPersistAtRef.current
    const waitMs = Math.max(PERSIST_WINDOW_MS - elapsedMs, 0)

    if (waitMs > 0) {
      setPersistencia(prevState => ({ 
        ...prevState, 
        status: 'queued', 
        error: '',
        willRetry: false
      }))
      clearPersistTimer()
      persistTimerRef.current = setTimeout(() => {
        void flushPersistQueue()
      }, waitMs)
      return
    }

    void flushPersistQueue()
  }, [clearPersistTimer, flushPersistQueue])

  const resetPersistencia = useCallback(() => {
    clearPersistTimer()
    pendingPersistRef.current = null
    persistInFlightRef.current = false
    retryCountRef.current = 0
    lastPersistAtRef.current = 0
    lastPersistSignatureRef.current = ''
    setPersistencia({ 
      status: 'idle', 
      error: '',
      willRetry: false,
      canRetry: false,
      isForbidden: false,
      retryInSeconds: 0
    })
  }, [clearPersistTimer])

  useEffect(() => {
    if (!pontoId || !resultado || !lastPayload) return

    const payload = buildSalvarCalculoPayload(pontoId, lastPayload, resultado)
    const signature = JSON.stringify(payload)

    if (signature === lastPersistSignatureRef.current) return

    pendingPersistRef.current = {
      pontoId,
      payload,
      signature,
    }
    if (autoSave) {
      schedulePersistQueue()
    } else {
      setPersistencia(prev => ({ ...prev, status: 'queued' })) // Indica que há mudanças pendentes
    }
  }, [lastPayload, pontoId, resultado, schedulePersistQueue, autoSave])

  useEffect(() => {
    return () => {
      clearPersistTimer()
    }
  }, [clearPersistTimer])

  return {
    persistencia,
    resetPersistencia,
    flushPersistQueue,
  }
}
