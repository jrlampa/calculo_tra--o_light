import { useState, useEffect, useRef, useCallback } from 'react'

/**
 * Hook customizado para monitoramento de performance
 * @returns {Object} - Métricas e funções de performance
 */
export const usePerformanceMonitor = () => {
  const [metrics, setMetrics] = useState({
    renderCount: 0,
    lastRenderTime: 0,
    averageRenderTime: 0,
    slowRenders: []
  })
  
  const renderStartTime = useRef(Date.now())
  const renderTimes = useRef([])

  useEffect(() => {
    const renderTime = Date.now() - renderStartTime.current
    renderTimes.current.push(renderTime)
    
    // Manter apenas as últimas 100 renderizações
    if (renderTimes.current.length > 100) {
      renderTimes.current = renderTimes.current.slice(-100)
    }
    
    const averageRenderTime = renderTimes.current.reduce((a, b) => a + b, 0) / renderTimes.current.length
    const slowRenders = renderTimes.current.filter(time => time > 16) // > 16ms = 60fps
    
    setMetrics(prev => ({
      renderCount: prev.renderCount + 1,
      lastRenderTime: renderTime,
      averageRenderTime,
      slowRenders: slowRenders.slice(-10) // Últimas 10 renderizações lentas
    }))
    
    renderStartTime.current = Date.now()
  })

  const startTimer = useCallback(() => {
    return performance.now()
  }, [])

  const endTimer = useCallback((startTime, label = 'Operation') => {
    const duration = performance.now() - startTime
    if (duration > 16) {
      console.warn(`Slow operation detected: ${label} took ${duration.toFixed(2)}ms`)
    }
    return duration
  }, [])

  const measureFunction = useCallback((fn, label = 'Function') => {
    return (...args) => {
      const start = startTimer()
      const result = fn(...args)
      const duration = endTimer(start, label)
      return { result, duration }
    }
  }, [startTimer, endTimer])

  return {
    metrics,
    startTimer,
    endTimer,
    measureFunction
  }
}

/**
 * Hook customizado para detectar re-renders desnecessários
 * @param {string} componentName - Nome do componente
 * @returns {Object} - Informações sobre re-renders
 */
export const useRerenderDetector = (componentName) => {
  const [rerenderCount, setRerenderCount] = useState(0)
  const [lastRenderProps, setLastRenderProps] = useState(null)
  const [rerenderReasons, setRerenderReasons] = useState([])

  useEffect(() => {
    setRerenderCount(prev => prev + 1)
  })

  const trackProps = useCallback((props) => {
    if (lastRenderProps) {
      const reasons = []
      
      Object.keys(props).forEach(key => {
        if (props[key] !== lastRenderProps[key]) {
          reasons.push(`${key}: ${JSON.stringify(lastRenderProps[key])} → ${JSON.stringify(props[key])}`)
        }
      })
      
      if (reasons.length > 0) {
        setRerenderReasons(prev => [...prev.slice(-5), {
          count: rerenderCount,
          reasons,
          timestamp: Date.now()
        }])
      }
    }
    
    setLastRenderProps(props)
  }, [lastRenderProps, rerenderCount])

  return {
    rerenderCount,
    rerenderReasons,
    trackProps
  }
}

/**
 * Hook customizado para otimização de listas grandes
 * @param {Array} items - Items da lista
 * @param {number} threshold - Limite para virtualização
 * @returns {Object} - Items otimizados e funções
 */
export const useVirtualizedList = (items = [], threshold = 100) => {
  const [visibleRange, setVisibleRange] = useState({ start: 0, end: threshold })
  const [containerHeight, setContainerHeight] = useState(0)
  const itemHeight = 40 // Altura aproximada de cada item

  const visibleItems = useMemo(() => {
    if (items.length <= threshold) {
      return items
    }
    
    return items.slice(visibleRange.start, visibleRange.end)
  }, [items, visibleRange, threshold])

  const handleScroll = useCallback((e) => {
    if (items.length <= threshold) return
    
    const scrollTop = e.target.scrollTop
    const start = Math.floor(scrollTop / itemHeight)
    const end = Math.min(start + threshold * 2, items.length)
    
    setVisibleRange({ start, end })
  }, [items.length, threshold])

  const scrollToIndex = useCallback((index) => {
    const container = document.querySelector('[data-virtualized-list]')
    if (container) {
      container.scrollTop = index * itemHeight
    }
  }, [])

  return {
    visibleItems,
    containerHeight: items.length * itemHeight,
    handleScroll,
    scrollToIndex,
    isVirtualized: items.length > threshold
  }
}
