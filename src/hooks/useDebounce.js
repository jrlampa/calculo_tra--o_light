/**
 * The provided code contains custom hooks for debouncing and throttling callbacks in React.
 * @param value - The `value` parameter in the `useDebounce` hook is the value that you want to
 * debounce. This can be any type of value such as a string, number, object, or array. The purpose of
 * debouncing a value is to delay its update until a certain amount of time has
 * @param delay - The `delay` parameter in the custom hooks `useDebounce`, `useDebouncedCallback`, and
 * `useThrottledCallback` represents the time interval in milliseconds for which the debounce or
 * throttle should be applied before executing the callback function or updating the value.
 * @returns For the `useDebounce` hook, it returns the debounced value after the specified delay.
 */
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
