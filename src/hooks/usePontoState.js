/**
 * The function `usePontoState` manages the state and logic related to creating and confirming points
 * in a project, including handling post details, confirming points, resetting point state, and
 * providing feedback to the user.
 * @returns The `usePontoState` custom hook is returning an object with the following properties:
 */
import { useState, useCallback, useMemo, useEffect } from 'react'
import { createPonto } from '../services/calculoApi.js'
import { POSTE_INICIAL } from '../features/calculo/formConfig.js'
import { trackUxFunnelEvent, UX_FUNNEL_EVENTS } from '../services/uxFunnelInstrumentation.js'

export const usePontoState = ({ projetoAtual, cabecalho, resetPersistencia }) => {
  const [poste, setPoste] = useState(() => ({ ...POSTE_INICIAL }))
  const [pontoAtual, setPontoAtual] = useState(null)
  const [pontoSnapshot, setPontoSnapshot] = useState(null)
  const [pontoState, setPontoState] = useState({ loading: false, status: 'idle', error: '' })

  // Memoizar validações
  const canConfirmPonto = useMemo(() => {
    return Boolean(
      projetoAtual?.id &&
      (cabecalho.ponto || '').trim() &&
      poste.tipoPoste &&
      poste.modeloPoste &&
      !pontoAtual?.id &&
      !pontoState.loading
    )
  }, [projetoAtual?.id, cabecalho.ponto, poste.tipoPoste, poste.modeloPoste, pontoAtual?.id, pontoState.loading])

  // Handler para atualizar campos do poste
  const handlePoste = useCallback((campo, valor) => {
    setPoste(prev => {
      if (campo === 'tipoPoste') {
        const tipoMudou = (prev.tipoPoste || '') !== valor
        return {
          ...prev,
          tipoPoste: valor,
          modeloPoste: tipoMudou ? '' : prev.modeloPoste,
        }
      }
      return { ...prev, [campo]: valor }
    })
  }, [])

  // Handler para confirmar ponto
  const handleConfirmPonto = useCallback(async () => {
    const ponto = (cabecalho.ponto || '').trim()

    if (!projetoAtual?.id) {
      setPontoState({ loading: false, status: 'error', error: 'Projeto ainda não foi criado.' })
      return
    }

    if (!ponto) {
      setPontoState({ loading: false, status: 'error', error: 'Informe o ponto antes de confirmar.' })
      return
    }

    if (!poste.tipoPoste || !poste.modeloPoste) {
      setPontoState({
        loading: false,
        status: 'error',
        error: 'Selecione o tipo e o modelo do poste antes de confirmar o ponto.',
      })
      return
    }

    setPontoState({ loading: true, status: 'saving', error: '' })

    try {
      const pontoCriado = await createPonto(projetoAtual.id, {
        ponto,
        tipoPoste: poste.tipoPoste,
        modeloPoste: poste.modeloPoste,
      })

      setPontoAtual(pontoCriado)
      setPontoSnapshot({
        ponto,
        tipoPoste: poste.tipoPoste || '',
        modeloPoste: poste.modeloPoste || '',
      })
      setPontoState({ loading: false, status: 'saved', error: '' })
      if (resetPersistencia) resetPersistencia()
      trackUxFunnelEvent(UX_FUNNEL_EVENTS.POINT_CONFIRMED, {
        projeto_id: projetoAtual?.id ?? null,
        ponto_id: pontoCriado?.id ?? null,
        ponto,
        tipo_poste: poste.tipoPoste || '',
        modelo_poste: poste.modeloPoste || '',
      })
    } catch (err) {
      setPontoState({ loading: false, status: 'error', error: err.message })
    }
  }, [projetoAtual, cabecalho.ponto, poste.tipoPoste, poste.modeloPoste, resetPersistencia])

  // Reset do estado do ponto
  const resetPonto = useCallback(() => {
    setPoste(() => ({ ...POSTE_INICIAL }))
    setPontoAtual(null)
    setPontoSnapshot(null)
    setPontoState({ loading: false, status: 'idle', error: '' })
  }, [])

  // Reset para próximo ponto (mantém projeto)
  const handleProximoPonto = useCallback(() => {
    setPoste(() => ({ ...POSTE_INICIAL }))
    setPontoAtual(null)
    setPontoSnapshot(null)
    setPontoState({ loading: false, status: 'idle', error: '' })
    if (resetPersistencia) resetPersistencia()
  }, [resetPersistencia])

  // Efeito para detectar mudanças APENAS no nome do ponto
  useEffect(() => {
    if (!pontoSnapshot) return

    const pontoMudou = (cabecalho.ponto || '').trim() !== pontoSnapshot.ponto
    
    // NOTA: Mudanças no poste.tipoPoste ou poste.modeloPoste NÃO reiniciam mais o ponto.
    // Isso evita o "Zera tudo" reportado pelo usuário e permite recalcular mantendo os vetores.
    if (!pontoMudou) return

    resetPonto()
  }, [cabecalho.ponto, pontoSnapshot, resetPonto])

  // Memoizar feedback do header
  const headerFeedback = useMemo(() => {
    if (pontoState.loading) {
      return { tone: 'saving', message: 'Vinculando ponto...' }
    }

    if (pontoState.error) {
      return { tone: 'error', message: pontoState.error }
    }

    if (!(cabecalho.ponto || '').trim()) {
      return { tone: 'idle', message: 'Informe o ponto para continuar.' }
    }

    if (!poste.tipoPoste || !poste.modeloPoste) {
      return { tone: 'idle', message: 'Selecione tipo e modelo do poste.' }
    }

    if (!pontoAtual?.id) {
      return { tone: 'idle', message: 'Ponto pendente de confirmação.' }
    }

    if (pontoState.status === 'saved') {
      return { tone: 'saved', message: `Ponto ${cabecalho.ponto} confirmado.` }
    }

    return { tone: 'saved', message: 'Ponto confirmado. Aguardando cálculo para salvar.' }
  }, [cabecalho.ponto, pontoAtual?.id, pontoState.error, pontoState.loading, pontoState.status, poste.modeloPoste, poste.tipoPoste])

  // Memoizar estado exportado
  const pontoStateMemo = useMemo(() => ({
    poste,
    pontoAtual,
    pontoSnapshot,
    pontoState,
    canConfirmPonto,
    headerFeedback,
    handlers: {
      handlePoste,
      handleConfirmPonto,
      resetPonto,
      handleProximoPonto
    }
  }), [poste, pontoAtual, pontoSnapshot, pontoState, canConfirmPonto, headerFeedback, handlePoste, handleConfirmPonto, resetPonto, handleProximoPonto])

  return pontoStateMemo
}
