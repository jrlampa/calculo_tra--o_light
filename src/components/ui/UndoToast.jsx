// UndoToast.jsx — Toast acessível para ação APAGA com janela de desfazer de 5 s
// Estados: idle (não renderiza) | undo_pending | committed | undone
import React, { useEffect, useRef } from 'react'

const UndoToast = ({
  clearState = 'idle',
  countdown = 0,
  onUndo,
}) => {
  const undoBtnRef = useRef(null)
  const previouslyFocusedRef = useRef(null)

  // Focus management: quando o toast abre, salva foco anterior e foca no "Desfazer"
  useEffect(() => {
    if (clearState === 'undo_pending') {
      previouslyFocusedRef.current = document.activeElement
      // Pequeno atraso para aguardar a renderização do botão
      requestAnimationFrame(() => {
        undoBtnRef.current?.focus()
      })
    }

    // Ao fechar (undone ou committed), devolve o foco ao campo anterior
    if (clearState === 'undone' || clearState === 'committed') {
      const target =
        previouslyFocusedRef.current instanceof HTMLElement
          ? previouslyFocusedRef.current
          : document.querySelector('[data-first-field]')

      if (target && typeof target.focus === 'function') {
        requestAnimationFrame(() => { target.focus() })
      }
      previouslyFocusedRef.current = null
    }
  }, [clearState])

  if (clearState === 'idle') return null

  const isPending   = clearState === 'undo_pending'
  const isUndone    = clearState === 'undone'
  const isCommitted = clearState === 'committed'

  const message = isPending
    ? `Dados técnicos serão apagados em ${countdown}s.`
    : isUndone
      ? 'Dados restaurados.'
      : 'Dados técnicos apagados.'

  return (
    <div
      className={`undo-toast undo-toast--${clearState}`}
      role="alertdialog"
      aria-modal="false"
      aria-live="assertive"
      aria-atomic="true"
      aria-label="Confirmação de limpeza de dados"
    >
      <span className="undo-toast__message">{message}</span>

      {isPending && (
        <button
          ref={undoBtnRef}
          type="button"
          className="undo-toast__btn"
          onClick={onUndo}
          aria-label="Desfazer limpeza de dados técnicos"
        >
          Desfazer
        </button>
      )}
    </div>
  )
}

export default React.memo(UndoToast)
