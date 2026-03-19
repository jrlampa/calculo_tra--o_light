// App.jsx — Aplicação principal de Cálculo de Tração de Rede Elétrica
import React, { useState, useMemo, useEffect } from 'react'
import useCalculo from './hooks/useCalculo.js'
import Header from './components/header/Header.jsx'
import RelogioAngulos from './components/relogio/RelogioAngulos.jsx'
import DiagramaPoste from './components/relogio/DiagramaPoste.jsx'
import TabelaCarga from './components/tabela/TabelaCarga.jsx'
import SecaoNivel from './components/secao/SecaoNivel.jsx'
import SecaoQDT from './components/secao/SecaoQDT.jsx'
import {
  dadosCabecalho,
  dadosPoste,
  dadosMT1,
  dadosMT2,
  dadosBT,
  dadosRamaisBTZero,
  dadosRamaisLigacao,
  tabelaCargas,
  resultante as resultanteMock,
} from './mockData.js'

const CAMPOS_MT = [
  { campo: 'tipoRede',       label: 'Tipo de rede',    unidade: '', isDropdown: true, configKey: 'redes' },
  { campo: 'tipoCabo',       label: 'Tipo de cabo',    unidade: '', isDropdown: true, configKey: 'cabos' },
  { campo: 'vao',            label: 'Vão',             unidade: 'm' },
  { campo: 'flecha',         label: 'Flecha',          unidade: 'm' },
  { campo: 'angulo',         label: 'Ângulo',          unidade: '°' },
  { campo: 'alturaPoste',    label: 'Altura poste',    unidade: 'm' },
  { campo: 'alturaAncoragem',label: 'Altura ancoragem',unidade: 'm' },
]

const CAMPOS_BT = CAMPOS_MT

const CAMPOS_BTZ = [
  { campo: 'qtdLigacoes',    label: 'Quantidade de ligações (*)', unidade: '' },
  { campo: 'vao',            label: 'Vão',             unidade: 'm' },
  { campo: 'flecha',         label: 'Flecha',          unidade: 'm' },
  { campo: 'angulo',         label: 'Ângulo',          unidade: '°' },
  { campo: 'alturaPoste',    label: 'Altura poste',    unidade: 'm' },
  { campo: 'alturaAncoragem',label: 'Altura ancoragem',unidade: 'm' },
]

const CAMPOS_RAL = [
  { campo: 'tipoCabo',       label: 'Tipo de cabo',    unidade: '', isDropdown: true, configKey: 'cabos' },
  { campo: 'qtdCabos',       label: 'Quantidade de cabos', unidade: '' },
  { campo: 'vao',            label: 'Vão',             unidade: 'm' },
  { campo: 'flecha',         label: 'Flecha',          unidade: 'm' },
  { campo: 'angulo',         label: 'Ângulo',          unidade: '°' },
  { campo: 'alturaPoste',    label: 'Altura poste',    unidade: 'm' },
  { campo: 'alturaAncoragem',label: 'Altura ancoragem',unidade: 'm' },
]

function updateTravessia(list, idx, campo, valor) {
  return list.map((t, i) => (i === idx ? { ...t, [campo]: valor } : t))
}

export default function App() {
  const [cabecalho, setCabecalho] = useState(dadosCabecalho)
  const [poste,     setPoste]     = useState(dadosPoste)
  const [mt1,       setMT1]       = useState(dadosMT1.travessias)
  const [mt2,       setMT2]       = useState(dadosMT2.travessias)
  const [bt,        setBT]        = useState(dadosBT.travessias)
  const [btz,       setBTZ]       = useState(dadosRamaisBTZero.travessias)
  const [ral,       setRAL]       = useState(dadosRamaisLigacao.travessias)
  const [config,    setConfig]    = useState({ redes: [], cabos: [], postes: {} })
  const [qdt,       setQDT]       = useState({
    v_nominal_mt: 13200,
    v_nominal_bt: 220,
    coef_perda: 75,
    reg_mt: 1.02,
    drop_mt_pct: 0,
    drop_trafo_pct: 0,
    drop_bt1_pct: 0,
    drop_bt2_pct: 0,
  })

  const formState = useMemo(
    () => ({ cabecalho, poste, mt1, mt2, bt, btz, ral }),
    [cabecalho, poste, mt1, mt2, bt, btz, ral]
  )

  useEffect(() => {
    fetch('/api/config')
      .then(res => res.json())
      .then(data => setConfig(data))
      .catch(err => console.error('Erro ao carregar config:', err))
  }, [])
  
  const { resultado, qdtResultado, loading } = useCalculo(formState, qdt)

  const vetoresTracao = useMemo(() => {
    if (!resultado?.vetores) return []
    const maxF = Math.max(...resultado.vetores.map(v => v.tracao_dan), 1)
    return resultado.vetores.map(v => ({
      angulo:    v.angulo_graus,
      magnitude: v.tracao_dan / maxF,
      label:     v.label,
    }))
  }, [resultado])

  const resultante = useMemo(() => {
    if (!resultado) return { angulo: 0, magnitude: 0 }
    const maxF = Math.max(...(resultado.vetores?.map(v => v.tracao_dan) ?? [1]), 1)
    return {
      angulo:    resultado.total_angulo_graus,
      magnitude: Math.min(resultado.total_tracao_dan / maxF, 1.5),
    }
  }, [resultado])

  const handleHeader = (campo, valor) => setCabecalho(prev => ({ ...prev, [campo]: valor }))
  const handlePoste  = (campo, valor) => setPoste(prev => ({ ...prev, [campo]: valor }))
  const handleQDT    = (campo, valor) => setQDT(prev => ({ ...prev, [campo]: valor }))

  const handleApaga = () => {
    const empty = arr => arr.map(t => Object.fromEntries(Object.keys(t).map(k => [k, ''])))
    setMT1(empty(mt1))
    setMT2(empty(mt2))
    setBT(empty(bt))
    setBTZ(empty(btz))
    setRAL(empty(ral))
    setPoste({ tipoPoste: '', modeloPoste: '', cargaNominal: '' })
  }

  return (
    <div className="page-wrap">
      <div className="flex gap-3">
        {/* ─── Coluna Esquerda ────────────────────────────── */}
        <div className="flex-1 min-w-0">
          <Header dados={cabecalho} onChange={handleHeader} />

          <div className="flex items-center gap-3 mb-2 mt-1">
            <div className="tracao-total-box flex-1">
              {loading ? 'Calculando…' : (resultado?.texto_total || 'TRAÇÃO TOTAL: 0 daN °')}
            </div>
            <div className="aprov-box" title="Aprovação" />
            <button className="btn-apaga" onClick={handleApaga}>
              APAGA
            </button>
          </div>

          <div className="flex items-center gap-2 mb-1">
            <span className="poste-lbl font-semibold">Tipo do Poste</span>
            <select
              className="xcell w-40"
              value={poste.tipoPoste}
              onChange={e => handlePoste('tipoPoste', e.target.value)}
            >
              <option value="">Selecione...</option>
              {Object.keys(config.postes).map(t => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
            <span className="poste-lbl font-semibold ml-2">Carga Nom.</span>
            <input
              className="xcell w-20"
              value={poste.cargaNominal}
              onChange={e => handlePoste('cargaNominal', e.target.value)}
            />
          </div>
          <div className="flex items-center gap-2 mb-2">
            <span className="poste-lbl font-semibold">Modelo do Poste</span>
            <select
              className="xcell w-full"
              value={poste.modeloPoste}
              onChange={e => handlePoste('modeloPoste', e.target.value)}
            >
              <option value="">Selecione...</option>
              {(config.postes[poste.tipoPoste] || []).map(m => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>

          <SecaoNivel
            titulo="MT - 1º Nível"
            labelResultado={resultado?.mt1?.texto || 'TRAÇÃO MT 1° NÍVEL (100 mm do topo):  daN °'}
            travessias={mt1}
            onChangeTravessia={(i, c, v) => setMT1(prev => updateTravessia(prev, i, c, v))}
            campos={CAMPOS_MT}
            config={config}
          />

          <SecaoNivel
            titulo="MT - 2º Nível"
            labelResultado={resultado?.mt2?.texto || 'TRAÇÃO MT 2° NÍVEL (100 mm do topo):  daN °'}
            travessias={mt2}
            onChangeTravessia={(i, c, v) => setMT2(prev => updateTravessia(prev, i, c, v))}
            campos={CAMPOS_MT}
            config={config}
          />

          <SecaoNivel
            titulo="BT"
            labelResultado={resultado?.bt?.texto || 'TRAÇÃO BT (100 mm do topo):  daN °'}
            travessias={bt}
            onChangeTravessia={(i, c, v) => setBT(prev => updateTravessia(prev, i, c, v))}
            campos={CAMPOS_BT}
            config={config}
          />

          <SecaoNivel
            titulo="Ramais BTZero"
            labelResultado={resultado?.btz?.texto || 'TRAÇÃO RAMAIS BTZERO (100 mm do topo):  daN °'}
            travessias={btz}
            onChangeTravessia={(i, c, v) => setBTZ(prev => updateTravessia(prev, i, c, v))}
            campos={CAMPOS_BTZ}
            config={config}
            nota="(*) - Considerar: monofásico = 1 ligação; trifásico = 3 ligações"
          />

          <SecaoNivel
            titulo="Ramais de ligação"
            labelResultado={resultado?.ral?.texto || 'TRAÇÃO RAMAIS DE LIGAÇÃO (100 mm do topo):  daN °'}
            travessias={ral}
            onChangeTravessia={(i, c, v) => setRAL(prev => updateTravessia(prev, i, c, v))}
            campos={CAMPOS_RAL}
            config={config}
          />

          <SecaoQDT 
            dados={qdt} 
            onChange={handleQDT} 
            resultado={qdtResultado} 
          />
        </div>

        {/* ─── Coluna Direita ─────────────────────────────── */}
        <div className="flex flex-col items-center" style={{ minWidth: 230 }}>
          <div className="self-end mb-1">
            <button className="btn-apaga" onClick={handleApaga}>
              APAGA
            </button>
          </div>

          <RelogioAngulos vetores={vetoresTracao} resultante={resultante} />
          
          <div className="mt-4 w-full">
            <DiagramaPoste />
          </div>

          <div className="mt-4 w-full">
            <TabelaCarga dados={tabelaCargas} />
          </div>
        </div>
      </div>
    </div>
  )
}
