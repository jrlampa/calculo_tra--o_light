/* The above code is a React component named `Header` that represents a header section of a UI. It
includes fields for various data such as organization, project, point, address, etc. The component
also includes status chips (`VinculoChip` and `PersistenciaChip`) for displaying status messages
related to data persistence and confirmation. */
// Header.jsx — Cabeçalho fiel ao Excel: Órgão | N.S. | Projeto | Ponto / Endereço / Estudado por | Matrícula | Data
import React from 'react'

const Field = React.memo(({ label, id, value, onChange, colSpan = 1, readOnly = false }) => {
  const labelId = `${id}-label`

  return (
    <>
      <td 
        id={labelId}
        className="field-lbl"
      >
        {label}
      </td>
      <td 
        colSpan={colSpan}
        className="header-cell"
      >
        <input
          id={id}
          className={`xcell header-input${readOnly ? ' xcell-readonly' : ''}`}
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
    if (status === 'error' || status === 'invalidated') {return 'saving'}
    if (status === 'saved') {return 'saved'}
    if (status === 'saving') {return 'saving'}
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

// StatusChip para persistência com contrato completo de estados
const PersistenciaChip = React.memo(({
  status = 'idle',
  message = '',
  willRetry = false,
  isForbidden = false,
  onRetry = null,
  onReconfirmProjeto = null,
}) => {
  const toneClass = (() => {
    if (status === 'error') {return 'error'}
    if (status === 'saved') {return 'saved'}
    if (status === 'saving' || status === 'queued') {return 'saving'}
    return 'idle'
  })()

  // Compute which CTA to show
  // queued → "Reenviar"
  // error + !willRetry + !isForbidden → "Tentar novamente"
  // error + isForbidden → "Reconfirmar projeto"
  const showReenviar = status === 'queued' && onRetry
  const showTentarNovamente = status === 'error' && !willRetry && !isForbidden && onRetry
  const showReconfirmar = status === 'error' && isForbidden && onReconfirmProjeto

  return (
    <div
      className={`persistencia-chip-wrapper${willRetry ? ' willretry' : ''}${isForbidden ? ' forbidden' : ''}`}
    >
      <span
        className={`persistencia-chip header-status header-status--${toneClass}`}
        role="status"
        aria-live="polite"
        aria-atomic="true"
        id="header-persistencia-status"
      >
        {message || 'Aguardando envio.'}
      </span>
      {showReenviar && (
        <button
          type="button"
          className="header-retry-button"
          onClick={onRetry}
          aria-label="Reenviar cálculo imediatamente"
        >
          Reenviar
        </button>
      )}
      {showTentarNovamente && (
        <button
          type="button"
          className="header-retry-button"
          onClick={onRetry}
          aria-label="Tentar novamente a persistência do cálculo"
        >
          Tentar novamente
        </button>
      )}
      {showReconfirmar && (
        <button
          type="button"
          className="header-reconfirm-button"
          onClick={onReconfirmProjeto}
          aria-label="Reconfirmar projeto para tentar salvar novamente"
        >
          Reconfirmar projeto
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
  persistenciaIsForbidden = false,
  onRetryPersistencia = null,
  onReconfirmProjeto = null,
}) => {
  return (
    <div>
      <table className="header-data-table">
        <tbody>
          <tr>
            <Field label="Órgão:" id="orgao" value={dados.orgao} onChange={onChange} readOnly={readOnlyCommon} />
            <Field label="N.S.:" id="ns" value={dados.ns} onChange={onChange} readOnly={readOnlyCommon} />
            <Field label="Projeto:" id="projeto" value={dados.projeto} onChange={onChange} readOnly={readOnlyCommon} />
            <Field label="Ponto:" id="ponto" value={dados.ponto} onChange={onChange} />
          </tr>

          <tr>
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

          <tr>
            <Field
              label="Estudado por:"
              id="estudadoPor"
              value={dados.estudadoPor}
              onChange={onChange}
              colSpan={3}
              readOnly={readOnlyCommon}
            />
            <td colSpan={4} className="header-empty-cell" />
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
              isForbidden={persistenciaIsForbidden}
              onRetry={onRetryPersistencia}
              onReconfirmProjeto={onReconfirmProjeto}
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
    prevProps.persistenciaIsForbidden === nextProps.persistenciaIsForbidden &&
    prevProps.onRetryPersistencia === nextProps.onRetryPersistencia &&
    prevProps.onReconfirmProjeto === nextProps.onReconfirmProjeto
  )
})
