/**
 * useCalculo.js – React hook that sends form state to the FastAPI /calcular
 * endpoint and returns the computed resultado.
 */
import { useState, useEffect, useRef } from 'react'

import { buildCalculoRequest, calcular, extractSectionErrors } from '../services/calculoApi.js'
import { trackUxFunnelEvent, UX_FUNNEL_EVENTS } from '../services/uxFunnelInstrumentation.js'

export default function useCalculo(formState, debounceMs = 600, enabled = true) {
  const [resultado, setResultado] = useState(null)
  const [loading, setLoading]     = useState(false)
  const [error, setError]         = useState(null)
  const [fieldErrors, setFieldErrors] = useState(null)
  const [lastPayload, setLastPayload] = useState(null)
  const timerRef = useRef(null)
  const abortRef = useRef(null)

  useEffect(() => {
    if (!enabled) {
      if (timerRef.current) { clearTimeout(timerRef.current) }
      if (abortRef.current) { abortRef.current.abort() }
      setLoading(false)
      setError(null)
      setFieldErrors(null)
      setResultado(null)
      setLastPayload(null)
      return undefined
    }

    if (timerRef.current) { clearTimeout(timerRef.current) }

    timerRef.current = setTimeout(async () => {
      if (abortRef.current) { abortRef.current.abort() }
      const controller = new AbortController()
      abortRef.current = controller

      try {
        let payload
        try {
          payload = buildCalculoRequest(formState)
        } catch (vErr) {
          setError(vErr.message)
          setFieldErrors(null)
          setLoading(false)
          return
        }

        setLoading(true)
        setError(null)
        setFieldErrors(null)

        const data = await calcular(payload, controller.signal)
        setResultado(data)
        setLastPayload(payload)

        trackUxFunnelEvent(UX_FUNNEL_EVENTS.CALCULATION_SUCCEEDED, {
          total_tracao_dan: data?.total_tracao_dan ?? null,
          total_angulo_graus: data?.total_angulo_graus ?? null,
        })
      } catch (err) {
        if (err.name === 'AbortError') {
          // Request was intentionally cancelled — do not update error state;
          // setLoading(false) in finally still executes as expected.
          return
        }

        // Para erros 422: extrair erros por seção (validação Pydantic)
        if (err.status === 422) {
          const sectionErrors = extractSectionErrors(err.rawDetail)
          if (sectionErrors) {
            setFieldErrors(sectionErrors)
            setError('Verifique os campos indicados em vermelho.')
            return
          }
        }

        setError(err.message)
        setFieldErrors(null)
      } finally {
        setLoading(false)
      }
    }, debounceMs)

    return () => {
      if (timerRef.current) { clearTimeout(timerRef.current) }
      if (abortRef.current) { abortRef.current.abort() }
    }
  }, [debounceMs, enabled, formState])

  return { resultado, loading, error, fieldErrors, lastPayload }
}
