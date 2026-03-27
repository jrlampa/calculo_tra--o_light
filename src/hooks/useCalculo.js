/**
 * The `useCalculo` React hook sends form state to a FastAPI endpoint for computation and returns the
 * computed result along with loading and error states.
 * @param formState - The `formState` parameter in the `useCalculo` hook represents the state of a form
 * that contains the data needed for a calculation. This form state is used to build a request payload
 * that is sent to the FastAPI endpoint for computation. The form state typically includes the input
 * values required for
 * @param [debounceMs=600] - The `debounceMs` parameter in the `useCalculo` hook is used to specify the
 * delay in milliseconds before making the API request after the form state has been updated. This
 * delay helps in reducing the number of API calls made in quick succession, especially when the form
 * state is changing rapidly.
 * @param [enabled=true] - The `enabled` parameter in the `useCalculo` hook is a boolean value that
 * determines whether the hook should be active or not. When `enabled` is set to `true`, the hook will
 * send the form state to the FastAPI endpoint for calculation. If `enabled` is set to
 * @returns The `useCalculo` hook returns an object with the following properties:
 * - `resultado`: The computed result from the FastAPI endpoint.
 * - `loading`: A boolean indicating whether the request is currently loading.
 * - `error`: Any error message encountered during the request.
 * - `lastPayload`: The last payload sent to the FastAPI endpoint.
 */
/**
 * useCalculo.js – React hook that sends form state to the FastAPI /calcular
 * endpoint and returns the computed resultado.
 */
import { useState, useEffect, useRef } from 'react'
import { buildCalculoRequest, extractSectionErrors } from '../services/calculoApi.js'
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

        const response = await fetch('/api/calcular', {
          method:  'POST',
          headers: { 'Content-Type': 'application/json' },
          body:    JSON.stringify(payload),
          signal: controller.signal,
        })

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}))
          // For 422: extract section-level field errors (Pydantic validation)
          if (response.status === 422) {
            const sectionErrors = extractSectionErrors(errorData.detail)
            if (sectionErrors) {
              setFieldErrors(sectionErrors)
              // Provide a concise general message too
              setError('Verifique os campos indicados em vermelho.')
              setLoading(false)
              return
            }
          }
          const detail = typeof errorData.detail === 'string'
            ? errorData.detail
            : `Traction API error: ${response.status}`
          throw new Error(detail)
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
          setFieldErrors(null)
        }
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
