import { useCallback, useRef } from 'react'

/**
 * Hook customizado para callbacks otimizados com cache inteligente
 * @param {Function} fn - Função a ser memoizada
 * @param {Array} deps - Dependências
 * @returns {Function} - Função memoizada otimizada
 */
export const useOptimizedCallback = (fn, deps) => {
  const ref = useRef(fn)
  
  // Atualizar a referência da função quando as dependências mudam
  ref.current = fn
  
  return useCallback((...args) => {
    return ref.current(...args)
  }, deps)
}

/**
 * Hook customizado para callbacks com deep comparison de dependências
 * @param {Function} fn - Função a ser memoizada
 * @param {Array} deps - Dependências
 * @returns {Function} - Função memoizada com deep comparison
 */
export const useDeepCallback = (fn, deps) => {
  const prevDeps = useRef()
  const callbackRef = useRef(fn)
  
  // Deep comparison das dependências
  const depsChanged = !prevDeps.current || 
    deps.length !== prevDeps.current.length ||
    deps.some((dep, index) => {
      const prevDep = prevDeps.current[index]
      if (typeof dep === 'object' && typeof prevDep === 'object') {
        return JSON.stringify(dep) !== JSON.stringify(prevDep)
      }
      return dep !== prevDep
    })
  
  if (depsChanged) {
    prevDeps.current = deps
    callbackRef.current = fn
  }
  
  return useCallback((...args) => {
    return callbackRef.current(...args)
  }, [depsChanged])
}

/**
 * Hook customizado para evitar re-renders em cascata
 * @param {Object} state - Estado do componente
 * @returns {Object} - Estado estabilizado
 */
export const useStableState = (state) => {
  const stableRef = useRef({})
  const prevKeysRef = useRef(new Set())
  
  const currentKeys = new Set(Object.keys(state))
  
  // Verificar se as chaves mudaram
  const keysChanged = currentKeys.size !== prevKeysRef.current.size ||
    ![...currentKeys].every(key => prevKeysRef.current.has(key))
  
  if (keysChanged) {
    prevKeysRef.current = currentKeys
    stableRef.current = {}
  }
  
  // Atualizar apenas os valores que mudaram
  Object.keys(state).forEach(key => {
    if (stableRef.current[key] !== state[key]) {
      stableRef.current[key] = state[key]
    }
  })
  
  return stableRef.current
}

/**
 * Hook customizado para memoizar objetos complexos
 * @param {Object} obj - Objeto a ser memoizado
 * @returns {Object} - Objeto memoizado
 */
export const useStableObject = (obj) => {
  const ref = useRef(obj)
  
  // Deep comparison
  const objString = JSON.stringify(obj)
  if (ref.current && JSON.stringify(ref.current) === objString) {
    return ref.current
  }
  
  ref.current = obj
  return obj
}

/**
 * Hook customizado para memoizar arrays
 * @param {Array} arr - Array a ser memoizado
 * @returns {Array} - Array memoizado
 */
export const useStableArray = (arr) => {
  const ref = useRef(arr)
  
  // Comparação de arrays
  if (ref.current && 
      ref.current.length === arr.length &&
      ref.current.every((item, index) => item === arr[index])) {
    return ref.current
  }
  
  ref.current = arr
  return arr
}

/**
 * Hook customizado para throttling de eventos
 * @param {Function} fn - Função a ser throttled
 * @param {number} delay - Tempo de delay em ms
 * @returns {Function} - Função throttled
 */
export const useThrottledFn = (fn, delay) => {
  const lastRun = useRef(Date.now())
  const timeoutRef = useRef()
  
  return useCallback((...args) => {
    if (Date.now() - lastRun.current >= delay) {
      fn(...args)
      lastRun.current = Date.now()
    } else {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = setTimeout(() => {
        fn(...args)
        lastRun.current = Date.now()
      }, delay - (Date.now() - lastRun.current))
    }
  }, [fn, delay])
}

/**
 * Hook customizado para eventos de input otimizados
 * @param {Function} onChange - Função de onChange
 * @param {number} delay - Delay para debounce (padrão: 300ms)
 * @returns {Function} - Função de onChange otimizada
 */
export const useOptimizedInput = (onChange, delay = 300) => {
  const timeoutRef = useRef()
  
  return useCallback((event) => {
    const value = event.target.value
    
    clearTimeout(timeoutRef.current)
    timeoutRef.current = setTimeout(() => {
      onChange(value)
    }, delay)
  }, [onChange, delay])
}
