/**
 * This function defines a custom hook in React for managing state related to projects, including
 * handling project data, CRUD operations, and user interactions.
 * @returns The `useProjetoState` custom hook is returning an object with the following properties:
 */
import { useState, useCallback, useMemo } from 'react'
import { createProjeto, listProjetos, deleteProjeto, updateProjeto } from '../services/calculoApi.js'
import { CABECALHO_INICIAL } from '../features/calculo/formConfig.js'
import { trackUxFunnelEvent, UX_FUNNEL_EVENTS } from '../services/uxFunnelInstrumentation.js'

export const useProjetoState = () => {
  const [etapa, setEtapa] = useState('home') // Inicia no Dashboard
  const [cabecalho, setCabecalho] = useState(() => ({ ...CABECALHO_INICIAL }))
  const [projetoAtual, setProjetoAtual] = useState(null)
  const [projetoState, setProjetoState] = useState({ loading: false, error: '' })

  const canConfirmProjeto = useMemo(() => {
    return (cabecalho.projeto || '').trim() && !projetoState.loading
  }, [cabecalho.projeto, projetoState.loading])

  const handleHeader = useCallback((campo, valor) => {
    setCabecalho(prev => ({ ...prev, [campo]: valor }))
  }, [])

  // Inicia um NOVO rascunho (não salva no DB ainda)
  const handleIniciarNovoProjeto = useCallback(() => {
    setProjetoAtual(null) // null indica que é um rascunho novo
    setCabecalho({ ...CABECALHO_INICIAL })
    setEtapa('projeto')
    trackUxFunnelEvent(UX_FUNNEL_EVENTS.NEW_PROJECT_STARTED_LOCAL)
  }, [])

  // Confirmar dados iniciais do projeto (Ainda no modo Rascunho ou Persistência Inicial)
  const handleConfirmProjeto = useCallback(async () => {
    if (!(cabecalho.projeto || '').trim()) {
      setProjetoState({ loading: false, error: 'Informe o nome do projeto.' })
      return
    }

    // O usuário quer "Salvar localmente" primeiro. 
    // Então aqui apenas avançamos para o cálculo sem chamar a API.
    setEtapa('calculo')
    trackUxFunnelEvent(UX_FUNNEL_EVENTS.PROJECT_CONFIRMED, {
      projeto_nome: cabecalho.projeto,
      is_draft: !projetoAtual
    })
  }, [cabecalho, projetoAtual])

  // Abrir um projeto existente do Banco
  const handleAbrirProjeto = useCallback(async (projeto) => {
    setProjetoState({ loading: true, error: '' })
    try {
      setProjetoAtual(projeto)
      setCabecalho({
        orgao: projeto.orgao || '',
        ns: projeto.ns || '',
        projeto: projeto.nome || '',
        endereco: projeto.endereco || '',
        estudadoPor: projeto.estudado_por || '',
        matricula: projeto.matricula || '',
        data: projeto.data_estudo || '',
        ponto: ''
      })
      setEtapa('calculo')
      trackUxFunnelEvent(UX_FUNNEL_EVENTS.PROJECT_OPENED_FROM_DB, { id: projeto.id })
    } catch (err) {
      setProjetoState({ loading: false, error: 'Erro ao abrir projeto.' })
    } finally {
      setProjetoState(prev => ({ ...prev, loading: false }))
    }
  }, [])

  const handleExcluirProjeto = useCallback(async (id) => {
    await deleteProjeto(id)
    trackUxFunnelEvent(UX_FUNNEL_EVENTS.PROJECT_DELETED_FROM_DB, { id })
  }, [])

  const handleEditarProjeto = useCallback((projeto) => {
    setProjetoAtual(projeto)
    setCabecalho({
      orgao: projeto.orgao || '',
      ns: projeto.ns || '',
      projeto: projeto.nome || '',
      endereco: projeto.endereco || '',
      estudadoPor: projeto.estudado_por || '',
      matricula: projeto.matricula || '',
      data: projeto.data_estudo || '',
      ponto: ''
    })
    setEtapa('projeto')
  }, [])

  const handleGuestConfirm = useCallback(async () => {
    window.localStorage.setItem('guest_mode', 'true')
    setEtapa('calculo')
  }, [])

  const resetProjeto = useCallback(() => {
    setEtapa('home')
    setCabecalho(() => ({ ...CABECALHO_INICIAL }))
    setProjetoAtual(null)
    setProjetoState({ loading: false, error: '' })
  }, [])

  return useMemo(() => ({
    etapa,
    cabecalho,
    projetoAtual,
    projetoState,
    canConfirmProjeto,
    handlers: {
      handleHeader,
      handleConfirmProjeto,
      handleIniciarNovoProjeto,
      handleAbrirProjeto,
      handleExcluirProjeto,
      handleEditarProjeto,
      handleGuestConfirm,
      resetProjeto,
      setEtapa,
      listProjetos,
      createProjeto, // Adicionado para persistência em lote
      deleteProjeto,
      updateProjeto,
      setProjetoAtual,
    }
  }), [etapa, cabecalho, projetoAtual, projetoState, canConfirmProjeto, handleHeader, handleConfirmProjeto, handleIniciarNovoProjeto, handleAbrirProjeto, handleExcluirProjeto, handleEditarProjeto, handleGuestConfirm, resetProjeto])
}
