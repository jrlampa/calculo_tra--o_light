/**
 * useCalculo.js – React hook that sends form state to the FastAPI /calcular
 * endpoint and returns the computed resultado.
 */
import { useState, useEffect, useRef } from 'react'
import { buildCalculoRequest } from '../services/calculoApi.js'
import { trackUxFunnelEvent, UX_FUNNEL_EVENTS } from '../services/uxFunnelInstrumentation.js'

export default function useCalculo(formState, debounceMs = 600, enabled = true) {
  const [resultado, setResultado] = useState(null)
  const [loading, setLoading]     = useState(false)
  const [error, setError]         = useState(null)
  const [lastPayload, setLastPayload] = useState(null)
  const timerRef = useRef(null)
  const abortRef = useRef(null)

  useEffect(() => {
    console.log('[useCalculo] Hook effect triggered. enabled:', enabled, 'hasFormState:', !!formState)
    if (!enabled) {
      if (timerRef.current) clearTimeout(timerRef.current)
      if (abortRef.current) abortRef.current.abort()
      setLoading(false)
      setError(null)
      setResultado(null)
      setLastPayload(null)
      return undefined
    }

    if (timerRef.current) clearTimeout(timerRef.current)

    timerRef.current = setTimeout(async () => {
      console.log('[useCalculo] runCalculation execution started (debounced)')
      if (abortRef.current) abortRef.current.abort()
      const controller = new AbortController()
      abortRef.current = controller
      
      try {
        let payload
        try {
          payload = buildCalculoRequest(formState)
        } catch (vErr) {
          console.error('[useCalculo] Validation Error in buildCalculoRequest:', vErr.message)
          setError(vErr.message)
          setLoading(false)
          return
        }

        console.log('[useCalculo] Executing fetch request to /api/calcular. Payload vao-t1:', payload?.mt1?.[0]?.vao)
        
        setLoading(true)
        setError(null)

        const response = await fetch('/api/calcular', {
          method:  'POST',
          headers: { 'Content-Type': 'application/json' },
          body:    JSON.stringify(payload),
          signal: controller.signal,
        })

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}))
          throw new Error(errorData.detail || `Traction API error: ${response.status}`)
        }

        const data = await response.json()
        console.log('[useCalculo] SUCCESS: Received result from API. total_tracao:', data?.total_tracao_dan)
        setResultado(data)
        setLastPayload(payload)
        
        trackUxFunnelEvent(UX_FUNNEL_EVENTS.CALCULATION_SUCCEEDED, {
          total_tracao_dan: data?.total_tracao_dan ?? null,
          total_angulo_graus: data?.total_angulo_graus ?? null,
        })
      } catch (err) {
        if (err.name !== 'AbortError') {
          console.error('[useCalculo] FETCH ERROR:', err.message)
          setError(err.message)
        }
      } finally {
        setLoading(false)
      }
    }, debounceMs)

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
      if (abortRef.current) abortRef.current.abort()
    }
  }, [debounceMs, enabled, formState])

  return { resultado, loading, error, lastPayload }
}
