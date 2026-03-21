import { useState, useEffect, useCallback } from 'react'

/**
 * Hook customizado para debounce de valores
 * @param {any} value - Valor a ser debounceado
 * @param {number} delay - Tempo de delay em ms
 * @returns {any} - Valor debounceado
 */
export const useDebounce = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = useState(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}

/**
 * Hook customizado para debounce de callbacks
 * @param {Function} callback - Função a ser debounceada
 * @param {number} delay - Tempo de delay em ms
 * @param {Array} deps - Dependências do callback
 * @returns {Function} - Callback debounceado
 */
export const useDebouncedCallback = (callback, delay, deps = []) => {
  const [callbackRef, setCallbackRef] = useState(() => callback)

  useEffect(() => {
    setCallbackRef(() => callback)
  }, [callback])

  return useCallback((...args) => {
    const timeoutId = setTimeout(() => {
      callbackRef.current(...args)
    }, delay)

    return () => clearTimeout(timeoutId)
  }, [delay, ...deps])
}

/**
 * Hook customizado para throttle de callbacks
 * @param {Function} callback - Função a ser throttled
 * @param {number} delay - Tempo de delay em ms
 * @returns {Function} - Callback throttled
 */
export const useThrottledCallback = (callback, delay) => {
  const [lastCall, setLastCall] = useState(0)
  const [timeoutId, setTimeoutId] = useState(null)

  return useCallback((...args) => {
    const now = Date.now()
    
    if (now - lastCall >= delay) {
      callback(...args)
      setLastCall(now)
    } else if (!timeoutId) {
      const id = setTimeout(() => {
        callback(...args)
        setLastCall(Date.now())
        setTimeoutId(null)
      }, delay - (now - lastCall))
      setTimeoutId(id)
    }
  }, [callback, delay, lastCall, timeoutId])
}
