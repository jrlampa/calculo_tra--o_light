import { useState, useCallback, useMemo } from 'react'
import { createProjeto } from '../services/calculoApi.js'
import { CABECALHO_INICIAL } from '../features/calculo/formConfig.js'
import { trackUxFunnelEvent, UX_FUNNEL_EVENTS } from '../services/uxFunnelInstrumentation.js'

export const useProjetoState = () => {
  const [etapa, setEtapa] = useState('projeto')
  const [cabecalho, setCabecalho] = useState(() => ({ ...CABECALHO_INICIAL }))
  const [projetoAtual, setProjetoAtual] = useState(null)
  const [projetoState, setProjetoState] = useState({ loading: false, error: '' })

  // Memoizar validações
  const canConfirmProjeto = useMemo(() => {
    return (cabecalho.projeto || '').trim() && !projetoState.loading
  }, [cabecalho.projeto, projetoState.loading])

  // Handler para atualizar campos do cabeçalho
  const handleHeader = useCallback((campo, valor) => {
    setCabecalho(prev => ({ ...prev, [campo]: valor }))
  }, [])

  // Handler para confirmar projeto
  const handleConfirmProjeto = useCallback(async () => {
    if (!(cabecalho.projeto || '').trim()) {
      setProjetoState({ loading: false, error: 'Informe o nome do projeto antes de continuar.' })
      return
    }

    setProjetoState({ loading: true, error: '' })

    try {
      const projetoCriado = await createProjeto(cabecalho)
      setProjetoAtual(projetoCriado)
      // Limpar modo convidado se existir
      window.localStorage.removeItem('guest_mode')
      
      setCabecalho(prev => ({
        ...prev,
        projeto: projetoCriado.nome || prev.projeto,
        ponto: '',
      }))
      setEtapa('calculo')
      setProjetoState({ loading: false, error: '' })
      trackUxFunnelEvent(UX_FUNNEL_EVENTS.PROJECT_CONFIRMED, {
        projeto_id: projetoCriado?.id ?? null,
        projeto_nome: projetoCriado?.nome || cabecalho.projeto || '',
      })
    } catch (err) {
      setProjetoState({ loading: false, error: err.message })
    }
  }, [cabecalho])

  // Handler para entrar como convidado (bypass JWT)
  const handleGuestConfirm = useCallback(async () => {
    setProjetoState({ loading: true, error: '' })
    try {
      window.localStorage.setItem('guest_mode', 'true')
      const guestCabecalho = {
        ...cabecalho,
        projeto: cabecalho.projeto || 'Projeto Convidado',
        orgao: cabecalho.orgao || 'CONVIDADO'
      }
      const projetoCriado = await createProjeto(guestCabecalho)
      setProjetoAtual(projetoCriado)
      setEtapa('calculo')
      setProjetoState({ loading: false, error: '' })
    } catch (err) {
      window.localStorage.removeItem('guest_mode')
      setProjetoState({ loading: false, error: `Modo convidado indisponível: ${err.message}` })
    }
  }, [cabecalho])

  // Reset do estado do projeto
  const resetProjeto = useCallback(() => {
    setEtapa('projeto')
    setCabecalho(() => ({ ...CABECALHO_INICIAL }))
    setProjetoAtual(null)
    setProjetoState({ loading: false, error: '' })
  }, [])

  // Memoizar estado exportado
  const projetoStateMemo = useMemo(() => ({
    etapa,
    cabecalho,
    projetoAtual,
    projetoState,
    canConfirmProjeto,
    handlers: {
      handleHeader,
      handleConfirmProjeto,
      handleGuestConfirm,
      resetProjeto,
      setEtapa
    }
  }), [etapa, cabecalho, projetoAtual, projetoState, canConfirmProjeto, handleHeader, handleConfirmProjeto, resetProjeto])

  return projetoStateMemo
}
