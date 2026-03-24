import { useState, useCallback, useMemo } from 'react'
import { useOptimizedCallback } from './useOptimizedCallbacks.js'
import {
  TRAVESSIA_BTZ_VAZIA,
  TRAVESSIA_MT_VAZIA,
  TRAVESSIA_RAL_VAZIA,
  createTravessiasVazias,
  updateTravessia,
} from '../features/calculo/formConfig.js'
import { POSTE_INICIAL } from '../features/calculo/formConfig.js'

export const useFormState = () => {
  const [mt1, setMT1] = useState(() => createTravessiasVazias(TRAVESSIA_MT_VAZIA))
  const [mt2, setMT2] = useState(() => createTravessiasVazias(TRAVESSIA_MT_VAZIA))
  const [bt, setBT] = useState(() => createTravessiasVazias(TRAVESSIA_MT_VAZIA))
  const [btz, setBTZ] = useState(() => createTravessiasVazias(TRAVESSIA_BTZ_VAZIA))
  const [ral, setRAL] = useState(() => createTravessiasVazias(TRAVESSIA_RAL_VAZIA))

  // Memoizar estado do formulário com estabilização
  const formState = useMemo(() => ({
    mt1,
    mt2,
    bt,
    btz,
    ral
  }), [mt1, mt2, bt, btz, ral])

  // Handler genérico para atualizar travessias otimizado
  const handleTravessiaChange = useOptimizedCallback((nivel, index, campo, valor) => {
    const setters = {
      mt1: setMT1,
      mt2: setMT2,
      bt: setBT,
      btz: setBTZ,
      ral: setRAL
    }

    const setter = setters[nivel]
    if (setter) {
      setter(prev => updateTravessia(prev, index, campo, valor))
    }
  }, [])

  // Reset de todos os níveis otimizado
  const resetForm = useOptimizedCallback(() => {
    const empty = arr => arr.map(t => Object.fromEntries(Object.keys(t).map(k => [k, ''])))
    
    setMT1(empty(mt1))
    setMT2(empty(mt2))
    setBT(empty(bt))
    setBTZ(empty(btz))
    setRAL(empty(ral))
  }, [mt1, mt2, bt, btz, ral])

  // Reset para próximo ponto otimizado
  const resetFormParaProximoPonto = useOptimizedCallback(() => {
    resetForm()
  }, [resetForm])

  // Aplicar dados importados em massa
  const applyImportedData = useOptimizedCallback((data) => {
    if (data.mt1) setMT1(data.mt1)
    if (data.mt2) setMT2(data.mt2)
    if (data.bt) setBT(data.bt)
    if (data.btz) setBTZ(data.btz)
    if (data.ral) setRAL(data.ral)
  }, [])

  // Verificar se formulário tem dados otimizado
  const hasFormData = useMemo(() => {
    const checkNivel = (nivel) => {
      return nivel.some(travessia => 
        Object.values(travessia).some(value => value && value.toString().trim() !== '')
      )
    }

    return checkNivel(mt1) || checkNivel(mt2) || checkNivel(bt) || checkNivel(btz) || checkNivel(ral)
  }, [mt1, mt2, bt, btz, ral])

  // Contar travessias preenchidas otimizado
  const travessiasPreenchidas = useMemo(() => {
    const count = (nivel) => {
      return nivel.filter(travessia => 
        Object.values(travessia).some(value => value && value.toString().trim() !== '')
      ).length
    }

    return {
      mt1: count(mt1),
      mt2: count(mt2),
      bt: count(bt),
      btz: count(btz),
      ral: count(ral),
      total: count(mt1) + count(mt2) + count(bt) + count(btz) + count(ral)
    }
  }, [mt1, mt2, bt, btz, ral])

  // Memoizar estado exportado com estabilização
  const formStateMemo = useMemo(() => ({
    formState,
    travessias: { 
      mt1,
      mt2,
      bt,
      btz,
      ral
    },
    hasFormData,
    travessiasPreenchidas,
    handlers: {
      handleTravessiaChange,
      resetForm,
      resetFormParaProximoPonto,
      applyImportedData
    }
  }), [formState, mt1, mt2, bt, btz, ral, hasFormData, travessiasPreenchidas, handleTravessiaChange, resetForm, resetFormParaProximoPonto])

  return formStateMemo
}
