import React from 'react'

export default function MobileActionBar({
  onConfirm,
  onRetry,
  onNextPoint,
  statusPersistencia = 'idle',
  canRetry = false,
  canNextPoint = false,
  isDisabled = false,
}) {
  const isSaving = statusPersistencia === 'saving' || isDisabled

  return (
    <>
      {/* Desktop: Botões flutuantes em corner */}
      <div className="hidden md:flex fixed bottom-6 right-6 gap-2 flex-col z-40">
        <button
          onClick={onConfirm}
          disabled={isSaving}
          title="Confirmar cálculo (Atalho: Enter)"
          className="px-4 py-2 bg-action-primary text-white rounded font-semibold text-sm
                     disabled:opacity-50 disabled:cursor-not-allowed
                     hover:enabled:bg-action-primary-hover
                     focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-border-focus"
          aria-label="Confirmar cálculo"
        >
          ✓ Confirmar
        </button>
        
        {canRetry && (
          <button
            onClick={onRetry}
            disabled={isSaving}
            title="Reenviar cálculo (Atalho: Ctrl+R)"
            className="px-4 py-2 bg-action-secondary text-white rounded font-semibold text-sm
                       disabled:opacity-50 disabled:cursor-not-allowed
                       hover:enabled:bg-action-secondary-hover
                       focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-border-focus"
            aria-label="Reenviar cálculo"
          >
            ↻ Reenviar
          </button>
        )}

        {canNextPoint && (
          <button
            onClick={onNextPoint}
            disabled={isSaving}
            title="Ir para próximo ponto (Atalho: N)"
            className="px-4 py-2 bg-gray-600 text-white rounded font-semibold text-sm
                       disabled:opacity-50 disabled:cursor-not-allowed
                       hover:enabled:bg-gray-700
                       focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-border-focus"
            aria-label="Próximo ponto"
          >
            → Próx. Ponto
          </button>
        )}
      </div>

      {/* Tablet: Barra full-width */}
      <div className="hidden sm:flex md:hidden fixed bottom-0 left-0 right-0 gap-2 p-3 
                      bg-surface-panel shadow-glass border-t border-gray-300 z-40
                      pb-[max(0.75rem,env(safe-area-inset-bottom))]">
        <button
          onClick={onConfirm}
          disabled={isSaving}
          title="Confirmar cálculo"
          className="flex-1 px-3 py-2 bg-action-primary text-white text-sm rounded font-semibold
                     disabled:opacity-50 disabled:cursor-not-allowed
                     hover:enabled:bg-action-primary-hover
                     focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-border-focus"
          aria-label="Confirmar cálculo"
        >
          ✓ Confirmar
        </button>

        {canRetry && (
          <button
            onClick={onRetry}
            disabled={isSaving}
            title="Reenviar cálculo"
            className="flex-1 px-3 py-2 bg-action-secondary text-white text-sm rounded font-semibold
                       disabled:opacity-50 disabled:cursor-not-allowed
                       hover:enabled:bg-action-secondary-hover
                       focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-border-focus"
            aria-label="Reenviar cálculo"
          >
            ↻ Reenviar
          </button>
        )}

        {canNextPoint && (
          <button
            onClick={onNextPoint}
            disabled={isSaving}
            title="Próximo ponto"
            className="flex-1 px-3 py-2 bg-gray-600 text-white text-sm rounded font-semibold
                       disabled:opacity-50 disabled:cursor-not-allowed
                       hover:enabled:bg-gray-700
                       focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-border-focus"
            aria-label="Próximo ponto"
          >
            → Próximo
          </button>
        )}
      </div>

      {/* Mobile: Stacked vertical */}
      <div className="sm:hidden fixed bottom-0 left-0 right-0 flex flex-col gap-2 p-2 
                      bg-surface-panel shadow-glass border-t border-gray-300 z-40
                      pb-[max(0.5rem,env(safe-area-inset-bottom))]">
        <button
          onClick={onConfirm}
          disabled={isSaving}
          title="Confirmar cálculo (✓)"
          className="w-full py-3 bg-action-primary text-white font-bold rounded
                     disabled:opacity-50 disabled:cursor-not-allowed
                     hover:enabled:bg-action-primary-hover
                     focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-border-focus
                     active:enabled:scale-95 transition-transform"
          aria-label="Confirmar cálculo"
        >
          ✓
        </button>

        {canRetry && (
          <button
            onClick={onRetry}
            disabled={isSaving}
            title="Reenviar cálculo (↻)"
            className="w-full py-3 bg-action-secondary text-white font-bold rounded
                       disabled:opacity-50 disabled:cursor-not-allowed
                       hover:enabled:bg-action-secondary-hover
                       focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-border-focus
                       active:enabled:scale-95 transition-transform"
            aria-label="Reenviar cálculo"
          >
            ↻
          </button>
        )}

        {canNextPoint && (
          <button
            onClick={onNextPoint}
            disabled={isSaving}
            title="Próximo ponto (→)"
            className="w-full py-3 bg-gray-600 text-white font-bold rounded
                       disabled:opacity-50 disabled:cursor-not-allowed
                       hover:enabled:bg-gray-700
                       focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-border-focus
                       active:enabled:scale-95 transition-transform"
            aria-label="Próximo ponto"
          >
            →
          </button>
        )}
      </div>
    </>
  )
}
