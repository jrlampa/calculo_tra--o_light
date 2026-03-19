/**
 * useCalculo.js – React hook that sends form state to the FastAPI /calcular
 * endpoint and returns the computed resultado.
 */
import { useState, useEffect, useRef } from 'react'

function _toFloat(v) {
  if (v === '' || v === null || v === undefined) return 0
  if (typeof v === 'number') return v
  const s = String(v).replace(',', '.')
  const n = parseFloat(s)
  return isNaN(n) ? 0 : n
}

function mapMT(t) {
  return {
    tipo_rede:         t.tipoRede       || '',
    tipo_cabo:         t.tipoCabo       || '',
    vao:               _toFloat(t.vao),
    flecha:            _toFloat(t.flecha),
    angulo:            _toFloat(t.angulo),
    altura_poste:      _toFloat(t.alturaPoste),
    altura_ancoragem:  _toFloat(t.alturaAncoragem),
  }
}

function mapBT(t) {
  return {
    tipo_rede:         t.tipoRede       || '',
    tipo_cabo:         t.tipoCabo       || '',
    vao:               _toFloat(t.vao),
    flecha:            _toFloat(t.flecha),
    angulo:            _toFloat(t.angulo),
    altura_poste:      _toFloat(t.alturaPoste),
    altura_ancoragem:  _toFloat(t.alturaAncoragem),
  }
}

function mapBTZ(t) {
  return {
    qtd_ligacoes:      _toFloat(t.qtdLigacoes),
    vao:               _toFloat(t.vao),
    flecha:            _toFloat(t.flecha),
    angulo:            _toFloat(t.angulo),
    altura_poste:      _toFloat(t.alturaPoste),
    altura_ancoragem:  _toFloat(t.alturaAncoragem),
  }
}

function mapRAL(t) {
  return {
    tipo_cabo:         t.tipoCabo       || '',
    qtd_cabos:         _toFloat(t.qtdCabos),
    vao:               _toFloat(t.vao),
    flecha:            _toFloat(t.flecha),
    angulo:            _toFloat(t.angulo),
    altura_poste:      _toFloat(t.alturaPoste),
    altura_ancoragem:  _toFloat(t.alturaAncoragem),
  }
}

export default function useCalculo(formState, qdtState, debounceMs = 600) {
  const [resultado, setResultado] = useState(null)
  const [qdtResultado, setQdtResultado] = useState(null)
  const [loading, setLoading]     = useState(false)
  const [error, setError]         = useState(null)
  const timerRef = useRef(null)
  const abortRef = useRef(null)

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current)

    timerRef.current = setTimeout(async () => {
      if (abortRef.current) abortRef.current.abort()
      const controller = new AbortController()
      abortRef.current = controller

      const { cabecalho, poste, mt1, mt2, bt, btz, ral } = formState

      setLoading(true)
      setError(null)

      try {
        // Parallel requests for Traction and QDT
        const [resTracao, resQdt] = await Promise.all([
          fetch('/api/calcular', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({
              cabecalho: {
                orgao:        cabecalho.orgao        || '',
                ns:           cabecalho.ns           || '',
                projeto:      cabecalho.projeto      || '',
                ponto:        cabecalho.ponto        || '',
                endereco:     cabecalho.endereco     || '',
                estudado_por: cabecalho.estudadoPor  || '',
                matricula:    cabecalho.matricula    || '',
                data:         cabecalho.data         || '',
              },
              poste: {
                tipo_poste:    poste.tipoPoste    || '',
                modelo_poste:  poste.modeloPoste  || '',
                carga_nominal: _toFloat(poste.cargaNominal),
              },
              mt1: mt1.map(mapMT),
              mt2: mt2.map(mapMT),
              bt:  bt.map(mapBT),
              btz: btz.map(mapBTZ),
              ral: ral.map(mapRAL),
            }),
            signal: controller.signal,
          }),
          fetch('/api/calcular/qdt', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({
              v_nominal_mt:   _toFloat(qdtState.v_nominal_mt),
              v_nominal_bt:   _toFloat(qdtState.v_nominal_bt),
              coef_perda:     _toFloat(qdtState.coef_perda),
              reg_mt:         _toFloat(qdtState.reg_mt),
              drop_mt_pct:    _toFloat(qdtState.drop_mt_pct),
              drop_trafo_pct: _toFloat(qdtState.drop_trafo_pct),
              drop_bt1_pct:   _toFloat(qdtState.drop_bt1_pct),
              drop_bt2_pct:   _toFloat(qdtState.drop_bt2_pct),
            }),
            signal: controller.signal,
          })
        ])

        if (!resTracao.ok) throw new Error(`Traction API error: ${resTracao.status}`)
        if (!resQdt.ok) throw new Error(`QDT API error: ${resQdt.status}`)

        const dataTracao = await resTracao.json()
        const dataQdt = await resQdt.json()

        setResultado(dataTracao)
        setQdtResultado(dataQdt)
      } catch (err) {
        if (err.name !== 'AbortError') setError(err.message)
      } finally {
        setLoading(false)
      }
    }, debounceMs)

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [JSON.stringify(formState), JSON.stringify(qdtState)])

  return { resultado, qdtResultado, loading, error }
}
