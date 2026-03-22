// Header.jsx — Cabeçalho fiel ao Excel: Órgão | N.S. | Projeto | Ponto / Endereço / Estudado por | Matrícula | Data
import React from 'react'

const Field = React.memo(({ label, id, value, onChange, colSpan = 1, readOnly = false }) => {
  const labelId = `${id}-label`

  return (
    <>
      <td 
        id={labelId}
        className="field-lbl" 
        style={{ 
          backgroundColor: '#E2E2E2', 
          border: '1px solid #999',
          textAlign: 'right',
          padding: '2px 4px',
          width: 80
        }}
      >
        {label}
      </td>
      <td 
        colSpan={colSpan}
        style={{ 
          border: '1px solid #999',
          padding: 0
        }}
      >
        <input
          id={id}
          className={`xcell header-input${readOnly ? ' xcell-readonly' : ''}`}
          style={{ 
            width: '100%', 
            border: 'none', 
            height: 18
          }}
          value={value ?? ''}
          onChange={readOnly ? undefined : e => onChange(id, e.target.value)}
          readOnly={readOnly}
          aria-labelledby={labelId}
          aria-label={label.replace(':', '')}
        />
      </td>
    </>
  )
})

// StatusChip separado para vínculo/ponto
const VinculoChip = React.memo(({ status = 'idle', message = '' }) => {
  const toneClass = (() => {
    if (status === 'error' || status === 'invalidated') return 'saving'
    if (status === 'saved') return 'saved'
    if (status === 'saving') return 'saving'
    return 'idle'
  })()

  return (
    <span
      className={`vinculo-chip header-status header-status--${toneClass}`}
      role="status"
      aria-live="polite"
      id="header-vinculo-status"
    >
      {message || 'Aguardando ponto…'}
    </span>
  )
})

// StatusChip para persistência com countdown opcional
const PersistenciaChip = React.memo(({ status = 'idle', message = '', willRetry = false, retryInSeconds = 0, onRetry = null }) => {
  const toneClass = (() => {
    if (status === 'error') return 'error'
    if (status === 'saved') return 'saved'
    if (status === 'saving' || status === 'queued') return 'saving'
    return 'idle'
  })()

  const displayMessage = willRetry
    ? `Nova tentativa em ${retryInSeconds}s...`
    : message || 'Aguardando envio.'

  return (
    <div
      className={`persistencia-chip-wrapper${willRetry ? ' willretry' : ''}`}
    >
      <span
        className={`persistencia-chip header-status header-status--${toneClass}`}
        role="status"
        aria-live="assertive"
        aria-atomic="true"
        id="header-persistencia-status"
      >
        {displayMessage}
      </span>
      {onRetry && status === 'error' && !willRetry && (
        <button
          type="button"
          className="header-retry-button"
          onClick={onRetry}
          aria-label="Tentar novamente a persistência do cálculo"
        >
          Tentar novamente
        </button>
      )}
    </div>
  )
})

const Header = ({
  dados,
  onChange,
  readOnlyCommon = false,
  // Vínculo/Ponto
  onConfirmPonto,
  confirmingPonto = false,
  pontoStatus = 'idle',
  pontoMensagem = '',
  canConfirmPonto = false,
  // Persistência
  persistenciaStatus = 'idle',
  persistenciaMensagem = '',
  persistenciaWillRetry = false,
  persistenciaRetryInSeconds = 0,
  onRetryPersistencia = null,
}) => {
  return (
    <div>
      <table style={{ borderCollapse: 'collapse', marginBottom: 8, width: '100%', tableLayout: 'fixed' }}>
        <tbody>
          <tr style={{ height: 22 }}>
            <Field label="Órgão:" id="orgao" value={dados.orgao} onChange={onChange} readOnly={readOnlyCommon} />
            <Field label="N.S.:" id="ns" value={dados.ns} onChange={onChange} readOnly={readOnlyCommon} />
            <Field label="Projeto:" id="projeto" value={dados.projeto} onChange={onChange} readOnly={readOnlyCommon} />
            <Field label="Ponto:" id="ponto" value={dados.ponto} onChange={onChange} />
          </tr>

          <tr style={{ height: 22 }}>
            <Field
              label="Endereço:"
              id="endereco"
              value={dados.endereco}
              onChange={onChange}
              colSpan={3}
              readOnly={readOnlyCommon}
            />
            <Field label="Matrícula:" id="matricula" value={dados.matricula} onChange={onChange} readOnly={readOnlyCommon} />
            <Field label="Data:" id="data" value={dados.data} onChange={onChange} readOnly={readOnlyCommon} />
          </tr>

          <tr style={{ height: 22 }}>
            <Field
              label="Estudado por:"
              id="estudadoPor"
              value={dados.estudadoPor}
              onChange={onChange}
              colSpan={3}
              readOnly={readOnlyCommon}
            />
            <td colSpan={4} style={{ border: '1px solid #999', backgroundColor: '#f9f9f9' }} />
          </tr>
        </tbody>
      </table>

      {onConfirmPonto ? (
        <>
          {/* Status row: dois chips lado a lado (vínculo + persistência) */}
          <div className="header-footer">
            <VinculoChip status={pontoStatus} message={pontoMensagem} />
            <PersistenciaChip
              status={persistenciaStatus}
              message={persistenciaMensagem}
              willRetry={persistenciaWillRetry}
              retryInSeconds={persistenciaRetryInSeconds}
              onRetry={onRetryPersistencia}
            />
            <button
              type="button"
              className="header-action-button"
              onClick={onConfirmPonto}
              disabled={!canConfirmPonto || confirmingPonto || pontoStatus === 'saved'}
              aria-describedby="header-vinculo-status header-persistencia-status"
            >
              {confirmingPonto ? 'Confirmando...' : pontoStatus === 'saved' && persistenciaStatus === 'saved' ? 'Salvo' : 'Confirmar ponto'}
            </button>
          </div>
        </>
      ) : null}
    </div>
  )
}

// Memoização com comparação customizada
export default React.memo(Header, (prevProps, nextProps) => {
  return (
    prevProps.dados === nextProps.dados &&
    prevProps.onChange === nextProps.onChange &&
    prevProps.readOnlyCommon === nextProps.readOnlyCommon &&
    prevProps.onConfirmPonto === nextProps.onConfirmPonto &&
    prevProps.confirmingPonto === nextProps.confirmingPonto &&
    prevProps.pontoStatus === nextProps.pontoStatus &&
    prevProps.pontoMensagem === nextProps.pontoMensagem &&
    prevProps.canConfirmPonto === nextProps.canConfirmPonto &&
    prevProps.persistenciaStatus === nextProps.persistenciaStatus &&
    prevProps.persistenciaMensagem === nextProps.persistenciaMensagem &&
    prevProps.persistenciaWillRetry === nextProps.persistenciaWillRetry &&
    prevProps.persistenciaRetryInSeconds === nextProps.persistenciaRetryInSeconds &&
    prevProps.onRetryPersistencia === nextProps.onRetryPersistencia
  )
})
