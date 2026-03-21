import { useState, useCallback, useMemo, useEffect } from 'react'
import { createPonto } from '../services/calculoApi.js'
import { POSTE_INICIAL } from '../features/calculo/formConfig.js'

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

  // Efeito para detectar mudanças no ponto atual
  useEffect(() => {
    if (!pontoSnapshot) return

    const pontoMudou = (cabecalho.ponto || '').trim() !== pontoSnapshot.ponto
    const tipoMudou = (poste.tipoPoste || '') !== pontoSnapshot.tipoPoste
    const modeloMudou = (poste.modeloPoste || '') !== pontoSnapshot.modeloPoste

    if (!pontoMudou && !tipoMudou && !modeloMudou) return

    resetPonto()
  }, [cabecalho.ponto, pontoSnapshot, poste.modeloPoste, poste.tipoPoste, resetPonto])

  // Memoizar feedback do header
  const headerFeedback = useMemo(() => {
    if (pontoState.loading) {
      return { tone: 'saving', message: 'Criando o ponto e vinculando ao projeto...' }
    }

    if (pontoState.error) {
      return { tone: 'error', message: pontoState.error }
    }

    if (!(cabecalho.ponto || '').trim()) {
      return { tone: 'idle', message: 'Informe o ponto e confirme para habilitar a persistência do cálculo.' }
    }

    if (!poste.tipoPoste || !poste.modeloPoste) {
      return { tone: 'idle', message: 'Selecione o tipo e o modelo do poste antes de confirmar o ponto.' }
    }

    if (!pontoAtual?.id) {
      return { tone: 'idle', message: 'Ponto pendente de confirmação.' }
    }

    if (pontoState.status === 'saved') {
      return { tone: 'saved', message: `Ponto ${cabecalho.ponto} confirmado.` }
    }

    return { tone: 'saved', message: 'Ponto confirmado. Aguardando o próximo retorno de cálculo para persistir.' }
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
