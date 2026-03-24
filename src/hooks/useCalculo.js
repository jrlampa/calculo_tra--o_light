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
      if (abortRef.current) abortRef.current.abort()
      const controller = new AbortController()
      abortRef.current = controller
      
      try {
        let payload
        try {
          payload = buildCalculoRequest(formState)
        } catch (vErr) {
          setError(vErr.message)
          setLoading(false)
          return
        }

        
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
        setResultado(data)
        setLastPayload(payload)
        
        trackUxFunnelEvent(UX_FUNNEL_EVENTS.CALCULATION_SUCCEEDED, {
          total_tracao_dan: data?.total_tracao_dan ?? null,
          total_angulo_graus: data?.total_angulo_graus ?? null,
        })
      } catch (err) {
        if (err.name !== 'AbortError') {
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
