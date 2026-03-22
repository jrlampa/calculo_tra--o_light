import { useMemo, useCallback, useEffect } from 'react'
import useCalculo from './useCalculo.js'
import usePersistenciaCalculo from './usePersistenciaCalculo.js'
import useUndoStack from './useUndoStack.js'
import { useProjetoState } from './useProjetoState.js'
import { usePontoState } from './usePontoState.js'
import { useFormState } from './useFormState.js'
import { useConfigState } from './useConfigState.js'
import { TABELA_CARGAS_POSTE } from '../constants/tabelaCargasPoste.js'
import { trackUxFunnelEvent, UX_FUNNEL_EVENTS } from '../services/uxFunnelInstrumentation.js'

export const useAppOptimizedState = () => {
  // Estado particionado
  const projetoState = useProjetoState()
  const formState = useFormState()
  const configState = useConfigState()

  useEffect(() => {
    trackUxFunnelEvent(UX_FUNNEL_EVENTS.FLOW_STARTED, {
      origin: 'app_loaded',
    })
  }, [])

  // Hooks existentes
  const { resultado, loading, error, lastPayload } = useCalculo(
    formState.formState,
    600,
    projetoState.etapa === 'calculo'
  )
  
  const { persistencia, resetPersistencia, flushPersistQueue } = usePersistenciaCalculo({
    pontoId: null, // Será atualizado quando o ponto for criado
    lastPayload,
    resultado,
  })

  // Estado do ponto com resetPersistencia injetado
  const pontoState = usePontoState({
    projetoAtual: projetoState.projetoAtual,
    cabecalho: projetoState.cabecalho,
    resetPersistencia
  })

  // Atualizar pontoId na persistência quando o ponto mudar
  useEffect(() => {
    // A persistência será atualizada automaticamente pelo hook usePersistenciaCalculo
    // através do pontoId que mudará no próximo render
  }, [pontoState.pontoAtual?.id])

  // Undo stack hook
  const { undoStack, undo, push: pushUndo, canUndo } = useUndoStack(
    pontoState.pontoAtual?.id,
    10,
    5 * 60 * 1000
  )

  // Global Ctrl+Z listener para undo
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
        e.preventDefault()
        const action = undo()
        if (action) {
          console.log(`Undo: ${action.fieldKey} ← ${action.oldValue}`)
          trackUxFunnelEvent(UX_FUNNEL_EVENTS.UNDO_APPLIED, {
            field_key: action.fieldKey,
          })
          // TODO: Implementar restauração específica do campo
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [undo])

  // Memoizar vetores de tração
  const vetoresTracao = useMemo(() => {
    if (!resultado?.vetores) return []
    const maxF = Math.max(...resultado.vetores.map(v => v.tracao_dan), 1)
    return resultado.vetores.map(v => ({
      angulo: v.angulo_graus,
      magnitude: v.tracao_dan / maxF,
      label: v.label,
    }))
  }, [resultado])

  // Memoizar resultante
  const resultante = useMemo(() => {
    if (!resultado) return { angulo: 0, magnitude: 0 }
    const maxF = Math.max(...(resultado.vetores?.map(v => v.tracao_dan) ?? [1]), 1)
    return {
      angulo: resultado.total_angulo_graus,
      magnitude: Math.min(resultado.total_tracao_dan / maxF, 1.5),
    }
  }, [resultado])

  // Memoizar feedback de persistência
  const persistenciaFeedback = useMemo(() => {
    if (persistencia.status === 'saving') {
      return { tone: 'saving', message: 'Salvando cálculo...' }
    }

    if (persistencia.status === 'queued') {
      return { tone: 'saving', message: 'Na fila. Salvando em instantes.' }
    }

    if (persistencia.status === 'error') {
      if (persistencia.isForbidden) {
        return {
          tone: 'error',
          message: 'Sem permissão para salvar este ponto. Reconfirme o projeto.',
        }
      }
      return {
        tone: 'error',
        message: persistencia.error ? `Falha ao salvar: ${persistencia.error}` : 'Falha ao salvar. Tente novamente.',
      }
    }

    if (persistencia.status === 'saved') {
      return { tone: 'saved', message: 'Cálculo salvo.' }
    }

    return { tone: 'idle', message: 'Aguardando envio.' }
  }, [persistencia.error, persistencia.isForbidden, persistencia.status])

  // Handler para apagar dados
  const handleApaga = useCallback(() => {
    formState.handlers.resetForm()
    pontoState.handlers.resetPonto()
    resetPersistencia()
  }, [formState.handlers, pontoState.handlers, resetPersistencia])

  // Handler para próximo ponto
  const handleProximoPonto = useCallback(() => {
    trackUxFunnelEvent(UX_FUNNEL_EVENTS.NEXT_POINT_CLICKED, {
      projeto_id: projetoState.projetoAtual?.id ?? null,
      ponto_id: pontoState.pontoAtual?.id ?? null,
    })
    formState.handlers.resetFormParaProximoPonto()
    pontoState.handlers.handleProximoPonto()
    projetoState.handlers.handleHeader('ponto', '')
  }, [formState.handlers, pontoState.handlers, projetoState.handlers, projetoState.projetoAtual?.id, pontoState.pontoAtual?.id])

  const handleManualPersistRetry = useCallback(() => {
    trackUxFunnelEvent(UX_FUNNEL_EVENTS.PERSIST_RETRY_MANUAL, {
      projeto_id: projetoState.projetoAtual?.id ?? null,
      ponto_id: pontoState.pontoAtual?.id ?? null,
      persist_status: persistencia.status,
    })
    void flushPersistQueue()
  }, [flushPersistQueue, persistencia.status, projetoState.projetoAtual?.id, pontoState.pontoAtual?.id])

  // Memoizar dados para componentes
  const dadosParaComponentes = useMemo(() => ({
    // Header
    header: {
      dados: projetoState.cabecalho,
      onChange: projetoState.handlers.handleHeader,
      readOnlyCommon: true,
      onConfirmPonto: pontoState.handlers.handleConfirmPonto,
      confirmingPonto: pontoState.pontoState.loading,
      pontoStatus: pontoState.headerFeedback.tone,
      pontoMensagem: pontoState.headerFeedback.message,
      persistenciaStatus: persistenciaFeedback.tone,
      persistenciaMensagem: persistenciaFeedback.message,
      persistenciaWillRetry: persistencia.willRetry,
      persistenciaRetryInSeconds: persistencia.retryInSeconds,
      canConfirmPonto: pontoState.canConfirmPonto,
      onRetryPersistencia: persistencia.status === 'error' && !persistencia.isForbidden && persistencia.canRetry
        ? handleManualPersistRetry
        : undefined,
    },
    
    // FlowStepper
    flowStepper: {
      etapaAtual: projetoState.etapa,
      statusVinculoPonto: pontoState.pontoState.status,
      resultado,
      statusPersistencia: persistencia.status,
      onNextPonto: persistencia.status === 'saved' ? handleProximoPonto : null,
      condensed: false,
    },
    
    // Poste selects
    poste: {
      tipoPoste: pontoState.poste.tipoPoste || '',
      modeloPoste: pontoState.poste.modeloPoste || '',
      onTipoChange: (valor) => pontoState.handlers.handlePoste('tipoPoste', valor),
      onModeloChange: (valor) => pontoState.handlers.handlePoste('modeloPoste', valor),
      tiposDisponiveis: configState.helpers.getTiposPoste(),
      modelosDisponiveis: configState.helpers.getModelosForTipo(pontoState.poste.tipoPoste),
    },
    
    // Seções de nível
    secoes: [
      {
        titulo: 'MT - 1º Nível',
        labelResultado: resultado?.mt1?.texto || 'TRAÇÃO MT 1° NÍVEL (100 mm do topo):  daN °',
        travessias: formState.travessias.mt1,
        onChangeTravessia: (i, c, v) => formState.handlers.handleTravessiaChange('mt1', i, c, v),
        campos: 'CAMPOS_MT', // Será importado
        config: configState.config,
      },
      {
        titulo: 'MT - 2º Nível',
        labelResultado: resultado?.mt2?.texto || 'TRAÇÃO MT 2° NÍVEL (100 mm do topo):  daN °',
        travessias: formState.travessias.mt2,
        onChangeTravessia: (i, c, v) => formState.handlers.handleTravessiaChange('mt2', i, c, v),
        campos: 'CAMPOS_MT',
        config: configState.config,
      },
      {
        titulo: 'BT',
        labelResultado: resultado?.bt?.texto || 'TRAÇÃO BT (100 mm do topo):  daN °',
        travessias: formState.travessias.bt,
        onChangeTravessia: (i, c, v) => formState.handlers.handleTravessiaChange('bt', i, c, v),
        campos: 'CAMPOS_BT',
        config: configState.config,
      },
      {
        titulo: 'Ramais BTZero',
        labelResultado: resultado?.btz?.texto || 'TRAÇÃO RAMAIS BTZERO (100 mm do topo):  daN °',
        travessias: formState.travessias.btz,
        onChangeTravessia: (i, c, v) => formState.handlers.handleTravessiaChange('btz', i, c, v),
        campos: 'CAMPOS_BTZ',
        config: configState.config,
        nota: '(*) - Considerar: monofásico = 1 ligação; trifásico = 3 ligações',
      },
      {
        titulo: 'Ramais de ligação',
        labelResultado: resultado?.ral?.texto || 'TRAÇÃO RAMAIS DE LIGAÇÃO (100 mm do topo):  daN °',
        travessias: formState.travessias.ral,
        onChangeTravessia: (i, c, v) => formState.handlers.handleTravessiaChange('ral', i, c, v),
        campos: 'CAMPOS_RAL',
        config: configState.config,
      },
    ],
    
    // Visualizações
    visualizacoes: {
      relogioAngulos: {
        vetores: vetoresTracao,
        resultante,
        resumoDados: resultado,
      },
      diagramaPoste: {},
      tabelaCarga: {
        dados: TABELA_CARGAS_POSTE,
      },
    },
    
    // Mobile Action Bar
    mobileActionBar: {
      onConfirm: () => flushPersistQueue(),
      onRetry: persistencia.canRetry ? handleManualPersistRetry : undefined,
      onNextPoint: persistencia.status === 'saved' ? handleProximoPonto : undefined,
      statusPersistencia: persistencia.status,
      canRetry: persistencia.canRetry && persistencia.status === 'error',
      canNextPoint: persistencia.status === 'saved',
      isDisabled: persistencia.status === 'saving',
    },
  }), [
    projetoState,
    pontoState,
    formState,
    configState,
    resultado,
    persistencia,
    vetoresTracao,
    resultante,
    persistenciaFeedback,
    handleProximoPonto,
    handleManualPersistRetry,
    flushPersistQueue
  ])

  // Memoizar estado completo
  const appState = useMemo(() => ({
    // Estados principais
    etapa: projetoState.etapa,
    loading,
    error,
    resultado,
    
    // Estados particionados
    projetoState,
    pontoState,
    formState,
    configState,
    
    // Estados auxiliares
    persistencia,
    undoStack,
    canUndo,
    vetoresTracao,
    resultante,
    
    // Feedback
    persistenciaFeedback,
    configBanner: configState.configBanner,
    
    // Handlers
    handlers: {
      ...projetoState.handlers,
      ...pontoState.handlers,
      ...formState.handlers,
      handleApaga,
      handleProximoPonto,
    },
    
    // Dados para componentes
    dadosParaComponentes,
    
    // Flags úteis
    flags: {
      isCalculoEtapa: projetoState.etapa === 'calculo',
      hasProjeto: !!projetoState.projetoAtual,
      hasPonto: !!pontoState.pontoAtual,
      hasFormData: formState.hasFormData,
      isConfigLoaded: configState.isConfigLoaded,
      canCalculate: projetoState.etapa === 'calculo' && pontoState.pontoAtual?.id,
    }
  }), [
    projetoState,
    pontoState,
    formState,
    configState,
    loading,
    error,
    resultado,
    persistencia,
    undoStack,
    canUndo,
    vetoresTracao,
    resultante,
    persistenciaFeedback,
    dadosParaComponentes
  ])

  return appState
}
