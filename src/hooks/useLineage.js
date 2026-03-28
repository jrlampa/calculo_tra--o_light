/**
 * useLineage — fetches and caches the cross-project lineage chain for a Poste.
 *
 * The chain is ordered oldest→newest (index 0 = root ancestor, last = current
 * poste).  Only fetches when a `posteId` is provided and that poste has a known
 * `origem_id` (lineage link), so the hook is a no-op for brand-new postes.
 *
 * Usage:
 *   const { chain, loading, error } = useLineage(pontoAtual?.id, pontoAtual?.origem_id)
 */
import { useState, useEffect, useCallback, useRef } from 'react'
import { obterLinhagem } from '../services/calculoApi.js'

/**
 * @param {string|null|undefined} posteId    UUID of the current Poste
 * @param {string|null|undefined} origemId   If null/undefined the hook does nothing
 * @returns {{ chain: Array, loading: boolean, error: string, profundidade: number }}
 */
export function useLineage(posteId, origemId) {
  const [chain, setChain] = useState([])
  const [profundidade, setProfundidade] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Prevent stale setState after unmount
  const mountedRef = useRef(true)
  useEffect(() => {
    mountedRef.current = true
    return () => { mountedRef.current = false }
  }, [])

  const fetchChain = useCallback(async (id) => {
    setLoading(true)
    setError('')
    try {
      const data = await obterLinhagem(id)
      if (!mountedRef.current) return
      setChain(data.chain ?? [])
      setProfundidade(data.profundidade ?? 0)
    } catch (err) {
      if (!mountedRef.current) return
      setError(err.message || 'Erro ao obter linhagem')
      setChain([])
    } finally {
      if (mountedRef.current) setLoading(false)
    }
  }, [])

  useEffect(() => {
    // Only fetch when this poste has a lineage link
    if (!posteId || !origemId) {
      setChain([])
      setProfundidade(0)
      setError('')
      return
    }
    fetchChain(posteId)
  }, [posteId, origemId, fetchChain])

  return { chain, profundidade, loading, error }
}
