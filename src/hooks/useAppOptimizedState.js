/**
 * The `useAppOptimizedState` function in the provided JavaScript code is a complex custom hook that
 * optimizes state management for a specific application by partitioning state, handling calculations,
 * persistence, undo functionality, and providing data for various components.
 * @returns The `useAppOptimizedState` hook returns an object with the following properties:
 */
import { useMemo, useCallback, useEffect, useRef } from 'react'

import { TABELA_CARGAS_POSTE } from '../constants/tabelaCargasPoste.js'
import { buildBatchPayload, batchSaveCalculo, listProjetos } from '../services/calculoApi.js'
import { trackUxFunnelEvent, UX_FUNNEL_EVENTS } from '../services/uxFunnelInstrumentation.js'

import useCalculo from './useCalculo.js'
import { useConfigState } from './useConfigState.js'
import { useFormState } from './useFormState.js'
import usePersistenciaCalculo from './usePersistenciaCalculo.js'
import { usePontoState } from './usePontoState.js'
import { useProjetoState } from './useProjetoState.js'
import useUndoClear from './useUndoClear.js'
import useUndoStack from './useUndoStack.js'


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

  // Proxy para quebrar dependência circular: 
  // pontoState -> resetPersistencia -> usePersistenciaCalculo -> resultado -> useCalculo -> fullFormState -> pontoState
  const resetPersistRef = useRef(null)
  const resetPersistenciaProxy = useCallback(() => resetPersistRef.current?.(), [])

  // 1. Estado do Ponto (Agora no topo para fornecer pontoState.poste ao cálculo)
  const pontoState = usePontoState({
    projetoAtual: projetoState.projetoAtual,
    cabecalho: projetoState.cabecalho,
    resetPersistencia: resetPersistenciaProxy
  })

  // 2. Estado completo para o cálculo (Unificado)
  const fullFormState = useMemo(() => ({
    cabecalho: projetoState.cabecalho,
    poste: pontoState.poste,
    ...formState.formState
  }), [projetoState.cabecalho, pontoState.poste, formState.formState])

  // 3. Motor de Cálculo
  const { resultado, loading, error, lastPayload } = useCalculo(
    fullFormState,
    600,
    projetoState.etapa === 'calculo'
  )
  
  // 4. Persistência (Depende de resultado e lastPayload)
  // Se for rascunho (projetoAtual é null), desativa autoSave
  const { persistencia, resetPersistencia, flushPersistQueue } = usePersistenciaCalculo({
    pontoId: pontoState.pontoAtual?.id,
    lastPayload,
    resultado,
    autoSave: !!projetoState.projetoAtual
  })

  // Vincular a implementação real ao proxy
  resetPersistRef.current = resetPersistencia

  // Undo stack hook
  const { undoStack, undo, push: pushUndo, canUndo } = useUndoStack(
    pontoState.pontoAtual?.id,
    10,
    5 * 60 * 1000
  )

  // Ref keeps the latest handleTravessiaChange available inside the keydown closure
  // without triggering re-registration of the listener on every render
  const handleTravessiaChangeRef = useRef(null)
  handleTravessiaChangeRef.current = formState.handlers.handleTravessiaChange

  // Ref to always read the latest travessias snapshot in handleTravessiaChangeWithUndo
  // without adding formState.travessias to the useCallback dependency array
  const travessiasRef = useRef(formState.travessias)
  travessiasRef.current = formState.travessias

  // Global Ctrl+Z listener para undo
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
        e.preventDefault()
        const action = undo()
        if (action) {
          trackUxFunnelEvent(UX_FUNNEL_EVENTS.UNDO_APPLIED, {
            field_key: action.fieldKey,
          })
          // Restaurar o campo: fieldKey formato "nivel:index:campo"
          const parts = action.fieldKey.split(':')
          if (parts.length === 3) {
            const [nivel, idxStr, campo] = parts
            const index = Number(idxStr)
            if (!Number.isNaN(index)) {
              handleTravessiaChangeRef.current?.(nivel, index, campo, action.oldValue)
            }
          }
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [undo])

  // Wrapper de handleTravessiaChange que registra a alteração no undo stack antes de aplicá-la
  const handleTravessiaChangeWithUndo = useCallback((nivel, index, campo, valor) => {
    // Capturar valor anterior via ref — evita recriar o callback a cada mudança de campo
    const nivelData = travessiasRef.current[nivel]
    const oldValue = nivelData?.[index]?.[campo] ?? ''

    // Só registrar no undo se o valor realmente mudou
    if (oldValue !== valor) {
      pushUndo(`${nivel}:${index}:${campo}`, oldValue, valor)
    }

    // Despachar para o handler real via ref (sempre atualizado, sem stale closure)
    handleTravessiaChangeRef.current?.(nivel, index, campo, valor)
  }, [pushUndo])  // travessiasRef e handleTravessiaChangeRef são refs, nunca entram no array

  // Memoizar vetores de tração
  const vetoresTracao = useMemo(() => {
    if (!resultado?.vetores) {return []}
    const maxF = Math.max(...resultado.vetores.map(v => v.tracao_dan), 1)
    return resultado.vetores.map(v => ({
      angulo: v.angulo_graus,
      magnitude: v.tracao_dan / maxF,
      label: v.label,
    }))
  }, [resultado])

  // Memoizar resultante
  const resultante = useMemo(() => {
    if (!resultado) {return { angulo: 0, magnitude: 0 }}
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

  // Snapshot for APAGA undo: saved before the clear is committed
  const apagaSnapshotRef = useRef(null)

  // Refs that keep the latest handlers for the useUndoClear callbacks.
  // This prevents stale closures across the 5-second undo window.
  const clearCommitFnsRef = useRef(null)
  clearCommitFnsRef.current = {
    resetForm:            formState.handlers.resetForm,
    resetPonto:           pontoState.handlers.resetPonto,
    restoreFormSnapshot:  formState.handlers.restoreFormSnapshot,
    resetPersistencia,
    projetoId: projetoState.projetoAtual?.id ?? null,
    pontoId:   pontoState.pontoAtual?.id ?? null,
  }

  // useUndoClear wires the 5-second APAGA undo window
  const { clearState, countdown, requestClear, undoClear } = useUndoClear({
    ttlMs: 5000,
    onCommit: useCallback(() => {
      // Timeout expired — apply the actual reset via the latest handler refs
      clearCommitFnsRef.current.resetForm()
      clearCommitFnsRef.current.resetPonto()
      clearCommitFnsRef.current.resetPersistencia()
      apagaSnapshotRef.current = null
      trackUxFunnelEvent(UX_FUNNEL_EVENTS.CLEAR_COMMITTED, {
        projeto_id: clearCommitFnsRef.current.projetoId,
        ponto_id:   clearCommitFnsRef.current.pontoId,
      })
    }, []),  // stable: all dependencies accessed via clearCommitFnsRef
    onUndo: useCallback(() => {
      // Restore snapshot taken before the clear via the latest handler refs
      if (apagaSnapshotRef.current) {
        clearCommitFnsRef.current.restoreFormSnapshot(apagaSnapshotRef.current)
        apagaSnapshotRef.current = null
      }
      trackUxFunnelEvent(UX_FUNNEL_EVENTS.CLEAR_UNDONE, {
        projeto_id: clearCommitFnsRef.current.projetoId,
        ponto_id:   clearCommitFnsRef.current.pontoId,
      })
    }, []),  // stable: all dependencies accessed via clearCommitFnsRef
  })

  // Handler para apagar dados — opens the 5-second undo window
  const handleApaga = useCallback(() => {
    // Capture snapshot BEFORE any reset
    apagaSnapshotRef.current = {
      mt1: formState.travessias.mt1,
      mt2: formState.travessias.mt2,
      bt:  formState.travessias.bt,
      btz: formState.travessias.btz,
      ral: formState.travessias.ral,
    }
    trackUxFunnelEvent(UX_FUNNEL_EVENTS.CLEAR_STARTED, {
      projeto_id: projetoState.projetoAtual?.id ?? null,
      ponto_id: pontoState.pontoAtual?.id ?? null,
    })
    requestClear()
  }, [formState.travessias, projetoState.projetoAtual?.id, pontoState.pontoAtual?.id, requestClear])

  // Handler mestre para PERSISTÊNCIA EM LOTE (Salvar Tudo)
  const handleSalvarTudo = useCallback(async () => {
    try {
      const projId = projetoState.projetoAtual?.id
      
      trackUxFunnelEvent(UX_FUNNEL_EVENTS.BATCH_SAVE_START, { projeto_id: projId })
      
      const payload = buildBatchPayload(
        projId,
        formState,
        resultado
      )

      const res = await batchSaveCalculo(payload)

      // Atualizar estados locais se for um novo projeto
      if (!projId && res.projeto_id) {
        // Buscar detalhes do projeto para o estado
        const todos = await listProjetos(100, 0)
        const novo = todos.find(p => p.id === res.projeto_id)
        if (novo) {
          projetoState.handlers.handleAbrirProjeto(novo)
        }
      }

      // Notificar sucesso via persistencia status
      trackUxFunnelEvent(UX_FUNNEL_EVENTS.BATCH_SAVE_SUCCESS)
      
      // Forçar refresh no dashboard se necessário ou apenas marcar como salvo
      // Para manter a UI reativa, poderíamos forçar um 'saved' no usePersistenciaCalculo
      // Mas o mais limpo é o componente saber que terminou.
      return res
    } catch (err) {
      trackUxFunnelEvent(UX_FUNNEL_EVENTS.BATCH_SAVE_ERROR, { error: err.message })
      throw err
    }
  }, [projetoState.projetoAtual?.id, projetoState.handlers, formState, resultado])

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

  // Handler para importar do Excel
  const handleImportarExcel = useCallback(async (file) => {
    if (!file) {return}

    const formData = new FormData()
    formData.append('file', file)

    try {
      trackUxFunnelEvent(UX_FUNNEL_EVENTS.IMPORT_EXCEL_STARTED, { filename: file.name })
      // Faz o upload para a nova rota
      const response = await fetch('/api/calcular/importar-excel', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Falha ao processar arquivo Excel')
      }

      const data = await response.json()

      // 1. Atualizar Cabecalho
      if (data.cabecalho) {
        Object.entries(data.cabecalho).forEach(([key, val]) => {
          if (val) {projetoState.handlers.handleHeader(key, val)}
        })
      }

      // 2. Atualizar Poste
      if (data.poste) {
        if (data.poste.tipo_poste) {pontoState.handlers.handlePoste('tipoPoste', data.poste.tipo_poste)}
        if (data.poste.modelo_poste) {pontoState.handlers.handlePoste('modeloPoste', data.poste.modelo_poste)}
      }

      // 3. Atualizar Travessias em massa
      formState.handlers.applyImportedData(data)
      
      trackUxFunnelEvent(UX_FUNNEL_EVENTS.IMPORT_EXCEL_SUCCESS, { filename: file.name })
    } catch (err) {
      trackUxFunnelEvent(UX_FUNNEL_EVENTS.IMPORT_EXCEL_FAILED, { error: err.message })
      // O erro será exibido pelo ErrorBoundary ou banner se necessário
    }
  }, [projetoState.handlers, pontoState.handlers, formState.handlers])

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
        onChangeTravessia: (i, c, v) => handleTravessiaChangeWithUndo('mt1', i, c, v),
        campos: 'CAMPOS_MT', // Será importado
        config: configState.config,
      },
      {
        titulo: 'MT - 2º Nível',
        labelResultado: resultado?.mt2?.texto || 'TRAÇÃO MT 2° NÍVEL (100 mm do topo):  daN °',
        travessias: formState.travessias.mt2,
        onChangeTravessia: (i, c, v) => handleTravessiaChangeWithUndo('mt2', i, c, v),
        campos: 'CAMPOS_MT',
        config: configState.config,
      },
      {
        titulo: 'BT',
        labelResultado: resultado?.bt?.texto || 'TRAÇÃO BT (100 mm do topo):  daN °',
        travessias: formState.travessias.bt,
        onChangeTravessia: (i, c, v) => handleTravessiaChangeWithUndo('bt', i, c, v),
        campos: 'CAMPOS_BT',
        config: configState.config,
      },
      {
        titulo: 'Ramais BTZero',
        labelResultado: resultado?.btz?.texto || 'TRAÇÃO RAMAIS BTZERO (100 mm do topo):  daN °',
        travessias: formState.travessias.btz,
        onChangeTravessia: (i, c, v) => handleTravessiaChangeWithUndo('btz', i, c, v),
        campos: 'CAMPOS_BTZ',
        config: configState.config,
        nota: '(*) - Considerar: monofásico = 1 ligação; trifásico = 3 ligações',
      },
      {
        titulo: 'Ramais de ligação',
        labelResultado: resultado?.ral?.texto || 'TRAÇÃO RAMAIS DE LIGAÇÃO (100 mm do topo):  daN °',
        travessias: formState.travessias.ral,
        onChangeTravessia: (i, c, v) => handleTravessiaChangeWithUndo('ral', i, c, v),
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
      onConfirm: handleSalvarTudo, // Agora usa o Salvar Tudo (que inclui criar projeto/ponto se necessário)
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
    handleSalvarTudo,
    handleTravessiaChangeWithUndo,
    flushPersistQueue
  ])

  // Memoizar estado completo
  return useMemo(() => ({
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
    
    // APAGA undo window
    clearState,
    countdown,
    undoClear,
    
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
      handleImportarExcel,
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
    clearState,
    countdown,
    undoClear,
    vetoresTracao,
    resultante,
    persistenciaFeedback,
    dadosParaComponentes
  ])
}
