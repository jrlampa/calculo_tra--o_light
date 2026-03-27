// FlowStepper.jsx — Stepper operacional: Projeto -> Ponto -> Cálculo -> Persistido
// Com suporte a navegação "Próximo ponto" após persistência bem-sucedida
import React from 'react'

const StepperDot = React.memo(({ active = false, done = false, error = false, condensed = false }) => {
  const statusClass = (() => {
    if (error) {return 'stepper-dot--error'}
    if (done) {return 'stepper-dot--done'}
    if (active) {return 'stepper-dot--active'}
    return 'stepper-dot--idle'
  })()

  const iconChar = done ? '✓' : error ? '✕' : ''

  return (
    <div className={`stepper-dot ${statusClass}${condensed ? ' stepper-dot--condensed' : ''}`}>
      {iconChar || '•'}
    </div>
  )
})

const StepperConnector = React.memo(({ done = false, error = false, condensed = false }) => {
  const statusClass = (() => {
    if (error) {return 'stepper-connector--error'}
    if (done) {return 'stepper-connector--done'}
    return 'stepper-connector--idle'
  })()

  return <div className={`stepper-connector ${statusClass}${condensed ? ' stepper-connector--condensed' : ''}`} />
})

const FlowStepper = ({
  etapaAtual = 'projeto',
  statusVinculoPonto = 'idle', // idle|saving|saved|error|invalidated
  resultado = null,
  statusPersistencia = 'idle', // idle|saving|queued|saved|error
  onNextPonto = null,
  onEndProject = null,
  condensed = false, // mobile condensed mode
}) => {
  // Mapeamento de etapa para índice
  const etapas = ['projeto', 'ponto', 'calculo', 'persistido']
  const idxEtapa = Math.max(0, etapas.indexOf(etapaAtual))

  // Status computado para cada etapa
  const statusProjeto = 'done' // projeto sempre concluído após transição
  const statusPonto = (() => {
    if (etapaAtual === 'projeto') {return 'idle'}
    if (statusVinculoPonto === 'error' || statusVinculoPonto === 'invalidated') {return 'error'}
    if (statusVinculoPonto === 'saved') {return 'done'}
    if (statusVinculoPonto === 'saving') {return 'active'}
    return 'idle'
  })()
  const statusCalculo = (() => {
    if (etapaAtual === 'projeto' || etapaAtual === 'ponto') {return 'idle'}
    if (!resultado) {return 'idle'}
    return 'active'
  })()
  const statusPersistido = (() => {
    if (etapaAtual !== 'calculo' && etapaAtual !== 'persistido') {return 'idle'}
    if (statusPersistencia === 'error') {return 'error'}
    if (statusPersistencia === 'saved') {return 'done'}
    if (statusPersistencia === 'saving' || statusPersistencia === 'queued') {return 'active'}
    return 'idle'
  })()

  const canShowNextPointButton = statusPersistencia === 'saved' && onNextPonto

  if (condensed) {
    // Modo mobile: dois chips lado a lado (etapa atual + próxima)
    const labelEtapaAtual = etapas[idxEtapa] || 'inicio'
    const labelProxima = etapas[idxEtapa + 1] || 'fim'

    return (
      <nav className="stepper-container--mobile" aria-label="Progresso do fluxo">
        <ol className="stepper-chips-row" role="list">
          <li
            className="stepper-chip stepper-chip--current"
            role="listitem"
            aria-current="step"
            aria-label={`Etapa atual: ${labelEtapaAtual}`}
          >
            <span className="stepper-chip-label">{labelEtapaAtual}</span>
          </li>
          <li aria-hidden="true" className="stepper-chip-arrow">→</li>
          <li
            className="stepper-chip stepper-chip--next"
            role="listitem"
            aria-label={`Próxima etapa: ${labelProxima}`}
          >
            <span className="stepper-chip-label">{labelProxima}</span>
          </li>
        </ol>
        {canShowNextPointButton && (
          <button
            type="button"
            className="stepper-next-point-btn"
            onClick={onNextPonto}
            aria-label="Confirmar ponto e continuar para o próximo"
          >
            Próximo ponto
          </button>
        )}
      </nav>
    )
  }

  // Modo desktop: 4 passos horizontais com conectores
  const stepperItems = [
    { label: 'Projeto', status: statusProjeto, idx: 0, key: 'projeto' },
    { label: 'Ponto', status: statusPonto, idx: 1, key: 'ponto' },
    { label: 'Cálculo', status: statusCalculo, idx: 2, key: 'calculo' },
    { label: 'Persistido', status: statusPersistido, idx: 3, key: 'persistido' },
  ]

  return (
    <nav className="stepper-container" aria-label="Progresso do fluxo de cálculo">
      <ol className="stepper-row" role="list">
        {stepperItems.map((item, i) => {
          const isActive = item.status === 'active'
          const isDone = item.status === 'done'
          const isError = item.status === 'error'
          const isCurrent = item.key === etapaAtual

          return (
            <React.Fragment key={item.label}>
              <li
                className="stepper-step"
                role="listitem"
                aria-current={isCurrent ? 'step' : undefined}
                aria-label={`Etapa ${i + 1}: ${item.label} — ${
                  isError ? 'erro' : isDone ? 'concluída' : isActive ? 'em andamento' : 'pendente'
                }`}
              >
                <StepperDot
                  step={item.status}
                  label={item.label}
                  active={isActive}
                  done={isDone}
                  error={isError}
                />
                <span className="stepper-label" aria-hidden="true">{item.label}</span>
              </li>
              {i < stepperItems.length - 1 && (
                <StepperConnector
                  done={isDone}
                  error={isError}
                />
              )}
            </React.Fragment>
          )
        })}
      </ol>

      {canShowNextPointButton && (
        <div className="stepper-actions">
          <button
            type="button"
            className="stepper-next-point-btn"
            onClick={onNextPonto}
            aria-label="Confirmar ponto e continuar para o próximo ponto"
          >
            Próximo ponto
          </button>
          {onEndProject && (
            <button
              type="button"
              className="stepper-end-project-btn"
              onClick={onEndProject}
              aria-label="Encerrar projeto e voltar ao cadastro"
            >
              Encerrar projeto
            </button>
          )}
        </div>
      )}
    </nav>
  )
}

// Memoização com comparação customizada
export default React.memo(FlowStepper, (prevProps, nextProps) => {
  return (
    prevProps.etapaAtual === nextProps.etapaAtual &&
    prevProps.statusVinculoPonto === nextProps.statusVinculoPonto &&
    prevProps.resultado === nextProps.resultado &&
    prevProps.statusPersistencia === nextProps.statusPersistencia &&
    prevProps.onNextPonto === nextProps.onNextPonto &&
    prevProps.onEndProject === nextProps.onEndProject &&
    prevProps.condensed === nextProps.condensed
  )
})
