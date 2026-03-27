/* This code snippet is a React functional component named `TelaProjetoInicial` that represents a
screen for initial project setup. Here's a breakdown of what the code is doing: */
import React, { useEffect, useRef } from 'react'

const CAMPOS_PROJETO = [
  { id: 'orgao', label: 'Órgão' },
  { id: 'ns', label: 'N.S.' },
  { id: 'projeto', label: 'Projeto', required: true },
  { id: 'endereco', label: 'Endereço', fullWidth: true },
  { id: 'estudadoPor', label: 'Estudado por' },
  { id: 'matricula', label: 'Matrícula' },
  { id: 'data', label: 'Data', placeholder: 'dd/mm/aaaa' },
]

export default function TelaProjetoInicial({ dados, onChange, onConfirm, onGuestConfirm, onBack, loading, error }) {
  const projetoInputRef = useRef(null)
  const projetoErrorId = 'project-projeto-error'
  const hasProjetoError = Boolean(error)

  useEffect(() => {
    projetoInputRef.current?.focus()
  }, [])

  useEffect(() => {
    if (hasProjetoError) {
      projetoInputRef.current?.focus()
    }
  }, [hasProjetoError])

  const handleSubmit = event => {
    event.preventDefault()
    onConfirm()
  }

  return (
    <section className="project-screen">
      <div className="project-card">
        <div className="project-heading">
          <span className="project-kicker">Fluxo inicial</span>
          <h1 className="project-title">Cadastro do projeto</h1>
          <p className="project-description">
            Preencha os dados comuns uma única vez. Na etapa seguinte, esses campos ficam em modo leitura
            e apenas o campo Ponto permanece editável para confirmar cada poste do projeto.
          </p>
        </div>

        <form className="project-form" onSubmit={handleSubmit} noValidate>
          {CAMPOS_PROJETO.map(({ id, label, fullWidth, required, placeholder }) => (
            <div key={id} className={`project-field${fullWidth ? ' project-field--full' : ''}`}>
              <label htmlFor={id}>{label}</label>
              <input
                id={id}
                className="project-input"
                value={dados[id] ?? ''}
                onChange={event => onChange(id, event.target.value)}
                required={required}
                placeholder={placeholder}
                autoComplete="off"
                autoFocus={id === 'projeto'}
                ref={id === 'projeto' ? projetoInputRef : undefined}
                aria-invalid={id === 'projeto' && hasProjetoError ? true : undefined}
                aria-describedby={id === 'projeto' ? projetoErrorId : undefined}
              />
              {id === 'projeto' && (
                <p
                  id={projetoErrorId}
                  className="project-error-message"
                  role="alert"
                  aria-live="assertive"
                >
                  {error || ''}
                </p>
              )}
            </div>
          ))}

          <div className="project-form-footer">
            <p className="project-helper">O projeto será mantido localmente até que você decida salvar todos os dados no banco.</p>
            <div className="project-form-actions flex gap-3">
              <button 
                type="button" 
                onClick={onBack}
                className="project-submit bg-gray-700 hover:bg-gray-600 border-gray-600"
                disabled={loading}
              >
                Voltar
              </button>

              <div className="flex flex-col gap-2 w-full">
                <button 
                  type="submit" 
                  id="project-submit-btn"
                  className="project-submit" 
                  disabled={loading}
                  aria-label={loading ? 'Preparando rascunho' : 'Iniciar cálculo'}
                >
                  {loading ? 'Preparando...' : 'Iniciar cálculo 🚀'}
                </button>

                {import.meta.env.DEV && (
                  <button
                    type="button"
                    className="text-xs text-gray-400 hover:text-gray-200 underline mt-1"
                    onClick={onGuestConfirm}
                    disabled={loading}
                  >
                    Bypass Login (Convidado)
                  </button>
                )}
              </div>
            </div>
          </div>
        </form>
      </div>
    </section>
  )
}