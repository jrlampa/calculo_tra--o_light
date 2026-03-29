/**
 * The `useConfigState` function in this code snippet manages the state and loading of technical
 * configuration data for types and models of utility poles.
 */
import { useState, useCallback, useMemo, useEffect } from 'react'

const createConfigInicial = () => ({
  redes: [],
  cabos: [],
  postes: {},
  cabos_por_rede: {},
})

const normalizeStringArray = value => (
  Array.isArray(value)
    ? value
      .filter(item => typeof item === 'string')
      .map(item => item.trim())
      .filter(Boolean)
    : []
)

const normalizeLookupObject = value => {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return {}
  }

  return Object.entries(value).reduce((acc, [key, options]) => {
    const normalizedKey = String(key).trim()
    if (!normalizedKey) {return acc}
    acc[normalizedKey] = normalizeStringArray(options)
    return acc
  }, {})
}

const normalizeConfigPayload = payload => {
  const data = payload && typeof payload === 'object' ? payload : {}

  return {
    redes: normalizeStringArray(data.redes),
    cabos: normalizeStringArray(data.cabos),
    postes: normalizeLookupObject(data.postes),
    cabos_por_rede: normalizeLookupObject(data.cabos_por_rede),
  }
}

export const useConfigState = () => {
  const [config, setConfig] = useState(() => createConfigInicial())
  const [configState, setConfigState] = useState({ status: 'idle', error: '' })

  // Memoizar banner de configuração
  const configBanner = useMemo(() => {
    if (configState.status === 'loading') {
      return {
        tone: 'loading',
        role: 'status',
        message: 'Carregando configuração técnica de tipo e modelo de poste...',
      }
    }

    if (configState.status === 'error') {
      return {
        tone: 'error',
        role: 'alert',
        message: `Falha ao carregar /api/config. ${configState.error}`,
      }
    }

    return null
  }, [configState.error, configState.status])

  // Carregar configuração
  const loadConfig = useCallback(async () => {
    setConfigState({ status: 'loading', error: '' })

    try {
      const response = await fetch('/api/config')
      if (!response.ok) {
        throw new Error('Falha ao carregar as configurações de rede e poste.')
      }

      const data = await response.json()
      const normalizedConfig = normalizeConfigPayload(data)

      setConfig(normalizedConfig)
      setConfigState({ status: 'success', error: '' })
    } catch (err) {
      const fallbackMessage = 'Não foi possível carregar as configurações técnicas. Tente novamente.'
      setConfigState({
        status: 'error',
        error: err instanceof Error && err.message ? err.message : fallbackMessage,
      })
    }
  }, [])

  // Retry configuração
  const retryConfig = useCallback(() => {
    loadConfig()
  }, [loadConfig])

  // Verificar se configuração está carregada
  const isConfigLoaded = useMemo(() => {
    return configState.status === 'success' && Object.keys(config.postes).length > 0
  }, [configState.status, config.postes])

  // Obter modelos de poste para um tipo
  const getModelosForTipo = useCallback((tipoPoste) => {
    return config.postes[tipoPoste] || []
  }, [config.postes])

  // Obter todos os tipos de poste
  const getTiposPoste = useCallback(() => {
    return Object.keys(config.postes)
  }, [config.postes])

  // Memoizar estado exportado
  const configStateMemo = useMemo(() => ({
    config,
    configState,
    configBanner,
    isConfigLoaded,
    handlers: {
      loadConfig,
      retryConfig
    },
    helpers: {
      getModelosForTipo,
      getTiposPoste
    }
  }), [config, configState, configBanner, isConfigLoaded, loadConfig, retryConfig, getModelosForTipo, getTiposPoste])

  // Carregar configuração ao montar
  useEffect(() => {
    loadConfig()
  }, [loadConfig])

  return configStateMemo
}
