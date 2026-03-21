import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useOptimizedCallback, useStableObject, useStableArray } from '@/hooks/useOptimizedCallbacks'

describe('useOptimizedCallbacks', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('useOptimizedCallback', () => {
    it('should return a stable callback reference', () => {
      const callback = vi.fn()
      
      const { result, rerender } = renderHook(
        ({ fn }) => useOptimizedCallback(fn, []),
        { initialProps: { fn: callback } }
      )
      
      const firstCallback = result.current
      
      // Rerender with same dependencies
      rerender({ fn: callback })
      
      expect(result.current).toBe(firstCallback)
    })

    it('should call the callback when invoked', () => {
      const callback = vi.fn()
      
      const { result } = renderHook(
        ({ fn }) => useOptimizedCallback(fn, []),
        { initialProps: { fn: callback } }
      )
      
      act(() => {
        result.current('test-arg')
      })
      
      expect(callback).toHaveBeenCalledWith('test-arg')
    })

    it('should create new callback when dependencies change', () => {
      const callback1 = vi.fn()
      const callback2 = vi.fn()
      
      const { result, rerender } = renderHook(
        ({ fn }) => useOptimizedCallback(fn, [fn]),
        { initialProps: { fn: callback1 } }
      )
      
      const firstCallback = result.current
      
      rerender({ fn: callback2 })
      
      expect(result.current).not.toBe(firstCallback)
    })
  })

  describe('useStableObject', () => {
    it('should return a stable object reference', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useStableObject(value),
        { initialProps: { value: { a: 1, b: 2 } } }
      )
      
      const firstObject = result.current
      
      // Rerender with same value
      rerender({ value: { a: 1, b: 2 } })
      
      expect(result.current).toBe(firstObject)
    })

    it('should create new object when value changes', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useStableObject(value),
        { initialProps: { value: { a: 1, b: 2 } } }
      )
      
      const firstObject = result.current
      
      rerender({ value: { a: 1, b: 3 } })
      
      expect(result.current).not.toBe(firstObject)
      expect(result.current).toEqual({ a: 1, b: 3 })
    })

    it('should handle undefined values', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useStableObject(value),
        { initialProps: { value: undefined } }
      )
      
      const firstObject = result.current
      
      rerender({ value: undefined })
      
      expect(result.current).toBe(firstObject)
    })
  })

  describe('useStableArray', () => {
    it('should return a stable array reference', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useStableArray(value),
        { initialProps: { value: [1, 2, 3] } }
      )
      
      const firstArray = result.current
      
      // Rerender with same value
      rerender({ value: [1, 2, 3] })
      
      expect(result.current).toBe(firstArray)
    })

    it('should create new array when value changes', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useStableArray(value),
        { initialProps: { value: [1, 2, 3] } }
      )
      
      const firstArray = result.current
      
      rerender({ value: [1, 2, 4] })
      
      expect(result.current).not.toBe(firstArray)
      expect(result.current).toEqual([1, 2, 4])
    })

    it('should handle empty arrays', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useStableArray(value),
        { initialProps: { value: [] } }
      )
      
      const firstArray = result.current
      
      rerender({ value: [] })
      
      expect(result.current).toBe(firstArray)
      expect(result.current).toEqual([])
    })
  })
})
