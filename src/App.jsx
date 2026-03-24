// App.jsx — Aplicação principal de Cálculo de Tração de Rede Elétrica (Otimizado)
import React, { useRef } from 'react'
import { useAppOptimizedState } from './hooks/useAppOptimizedState.js'
import Header from './components/header/Header.jsx'
import FlowStepper from './components/fluxo/FlowStepper.jsx'
import ErrorBoundary from './components/error/ErrorBoundary.jsx'
import TelaProjetoInicial from './components/projeto/TelaProjetoInicial.jsx'
import SecaoNivel from './components/secao/SecaoNivel.jsx'
import { 
  LazyTabelaCarga, 
  LazyDiagramaPoste, 
  LazyRelogioAngulos, 
  LazyMobileActionBar,
  preloadAllComponents 
} from './components/lazy/LazyComponents.jsx'
import { CAMPOS_MT, CAMPOS_BT, CAMPOS_BTZ, CAMPOS_RAL } from './features/calculo/formConfig.js'

// Preload components quando a aplicação iniciar
preloadAllComponents()

export default function App() {
  const appState = useAppOptimizedState()
  const fileInputRef = useRef(null)

  // Se estiver na etapa de projeto
  if (appState.etapa === 'projeto') {
    return (
      <TelaProjetoInicial
        dados={appState.projetoState.cabecalho}
        onChange={appState.projetoState.handlers.handleHeader}
        onConfirm={appState.projetoState.handlers.handleConfirmProjeto}
        onGuestConfirm={appState.projetoState.handlers.handleGuestConfirm}
        loading={appState.projetoState.projetoState.loading}
        error={appState.projetoState.projetoState.error}
      />
    )
  }

  // Renderizar etapa de cálculo
  return (
    <ErrorBoundary>
      <div className="page-wrap">
        <div className="calc-layout">
          <div className="calc-main-column">
            <FlowStepper {...appState.dadosParaComponentes.flowStepper} />

            <Header {...appState.dadosParaComponentes.header} />

            {appState.error ? (
              <div className="status-banner" role="alert">
                {appState.error}
              </div>
            ) : null}

            <div className="flex items-center gap-3 mb-2 mt-1">
              <div className={`tracao-total-box flex-1 ${
                appState.resultado?.status_poste === 'OK' ? 'tracao-total-box--ok' : 
                appState.resultado?.status_poste === 'TOLERANCIA' ? 'tracao-total-box--tolerancia' : ''
              }`}>
                {appState.loading ? 'Calculando…' : (appState.resultado?.texto_total || 'TRAÇÃO TOTAL: 0 daN °')}
              </div>
            </div>

            <div className="flex flex-col gap-1 mb-2">
              {appState.configBanner ? (
                <div
                  className={`config-status-banner config-status-banner--${appState.configBanner.tone}`}
                  role={appState.configBanner.role}
                  aria-live="polite"
                >
                  <span>{appState.configBanner.message}</span>
                  {appState.configState.configState.status === 'error' ? (
                    <button
                      type="button"
                      className="config-retry-button"
                      onClick={appState.configState.handlers.retryConfig}
                    >
                      Tentar novamente
                    </button>
                  ) : null}
                </div>
              ) : null}

              <div className="flex items-center gap-2">
                <span className="poste-lbl font-semibold" style={{ minWidth: '130px' }}>Tipo do Poste</span>
                <select
                  className="flex-1 p-1 border rounded xcell poste-select"
                  value={appState.dadosParaComponentes.poste.tipoPoste}
                  onChange={e => appState.dadosParaComponentes.poste.onTipoChange(e.target.value)}
                >
                  <option value="">Selecione...</option>
                  {appState.dadosParaComponentes.poste.tiposDisponiveis.map(t => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
              <div className="flex items-center gap-2">
                <span className="poste-lbl font-semibold" style={{ minWidth: '130px' }}>Modelo do Poste</span>
                <select
                  className="flex-1 p-1 border rounded xcell poste-select"
                  value={appState.dadosParaComponentes.poste.modeloPoste}
                  onChange={e => appState.dadosParaComponentes.poste.onModeloChange(e.target.value)}
                  aria-describedby="modelo-poste-helper"
                >
                  <option value="">Selecione...</option>
                  {appState.dadosParaComponentes.poste.modelosDisponiveis.map(m => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              </div>
              <p id="modelo-poste-helper" className="poste-helper-text">
                Ao alterar o tipo do poste, o modelo é limpo automaticamente para manter a integridade do ponto.
              </p>
            </div>

            {/* Renderizar seções de nível dinamicamente */}
            {appState.dadosParaComponentes.secoes.map((secao, index) => {
              let campos
              switch (secao.campos) {
                case 'CAMPOS_MT':
                  campos = CAMPOS_MT
                  break
                case 'CAMPOS_BT':
                  campos = CAMPOS_BT
                  break
                case 'CAMPOS_BTZ':
                  campos = CAMPOS_BTZ
                  break
                case 'CAMPOS_RAL':
                  campos = CAMPOS_RAL
                  break
                default:
                  campos = CAMPOS_MT
              }

              return (
                <SecaoNivel
                  key={index}
                  titulo={secao.titulo}
                  labelResultado={secao.labelResultado}
                  travessias={secao.travessias}
                  onChangeTravessia={secao.onChangeTravessia}
                  campos={campos}
                  config={secao.config}
                  nota={secao.nota}
                />
              )
            })}
          </div>

          <div className="calc-side-column">
            <div className="flex flex-col gap-2 mb-2">
              <input
                type="file"
                ref={fileInputRef}
                style={{ display: 'none' }}
                accept=".xlsm,.xlsx"
                onChange={(e) => {
                  if (e.target.files?.[0]) {
                    appState.handlers.handleImportarExcel(e.target.files[0])
                    e.target.value = '' // Reset para permitir re-importar o mesmo arquivo
                  }
                }}
              />
              <button 
                className="btn-importar w-full py-3 px-4 rounded-lg font-bold shadow-lg transition-all duration-300 transform hover:scale-105 active:scale-95 flex items-center justify-center gap-3 border-b-4"
                style={{ 
                  backgroundColor: '#1b5e20', 
                  color: '#e8f5e9',
                  borderColor: '#113e11',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.1)'
                }}
                onClick={() => fileInputRef.current?.click()}
              >
                <span style={{ fontSize: '1.2rem' }}>📥</span>
                <span>IMPORTAR PLANILHA LEGADA</span>
              </button>
              
              <button 
                className="btn-apaga w-full py-2 px-4 rounded-lg font-bold shadow-md transition-all hover:bg-red-800" 
                onClick={appState.handlers.handleApaga}
              >
                🗑️ LIMPAR TUDO
              </button>
            </div>

            <LazyRelogioAngulos {...appState.dadosParaComponentes.visualizacoes.relogioAngulos} />

            <div className="mt-4 w-full">
              <LazyDiagramaPoste {...appState.dadosParaComponentes.visualizacoes.diagramaPoste} />
            </div>

            <div className="mt-4 w-full">
              <LazyTabelaCarga {...appState.dadosParaComponentes.visualizacoes.tabelaCarga} />
            </div>

            {/* Mobile Action Bar */}
            {appState.etapa === 'calculo' && (
              <LazyMobileActionBar {...appState.dadosParaComponentes.mobileActionBar} />
            )}
          </div>
        </div>
      </div>
    </ErrorBoundary>
  )
}
