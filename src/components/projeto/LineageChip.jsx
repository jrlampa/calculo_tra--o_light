/**
 * LineageChip — compact badge that shows a Poste is a continuation of another project's pole.
 *
 * - Collapsed (default): "🔗 Continuação" chip
 * - Expanded (click): shows full ancestry chain, oldest → newest
 *
 * Props:
 *  - posteId  (string) current Poste UUID
 *  - origemId (string|null) parent Poste UUID — if null/undefined the chip renders nothing
 */
import React, { useState } from 'react'

import { useLineage } from '../../hooks/useLineage.js'

function formatDate(isoString) {
  if (!isoString) {return '—'}
  try {
    return new Date(isoString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    })
  } catch {
    return isoString
  }
}

export default function LineageChip({ posteId, origemId }) {
  const [expanded, setExpanded] = useState(false)
  const { chain, profundidade, loading, error } = useLineage(posteId, origemId)

  // Nothing to show if there's no lineage link
  if (!origemId) {return null}

  return (
    <div className="inline-block">
      {/* Collapsed chip */}
      {!expanded && (
        <button
          type="button"
          onClick={() => setExpanded(true)}
          aria-expanded="false"
          aria-label="Ver linhagem deste poste"
          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-blue-900/50 text-blue-300 border border-blue-700 hover:bg-blue-800/60 transition-colors"
        >
          🔗 Continuação
          {profundidade > 0 && (
            <span className="opacity-70">({profundidade})</span>
          )}
        </button>
      )}

      {/* Expanded panel */}
      {expanded && (
        <div
          role="region"
          aria-label="Linhagem cross-projeto"
          className="bg-gray-800/90 border border-blue-700/50 rounded-lg p-3 min-w-[260px] max-w-xs shadow-lg"
        >
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-semibold text-blue-300">🔗 Linhagem do poste</span>
            <button
              type="button"
              onClick={() => setExpanded(false)}
              aria-label="Fechar linhagem"
              className="text-gray-400 hover:text-white text-xs"
            >
              ✕
            </button>
          </div>

          {loading && (
            <p className="text-gray-400 text-xs">Carregando…</p>
          )}

          {error && (
            <p className="text-red-400 text-xs" role="alert">{error}</p>
          )}

          {!loading && !error && chain.length === 0 && (
            <p className="text-gray-500 text-xs">Sem histórico disponível.</p>
          )}

          {!loading && !error && chain.length > 0 && (
            <ol className="space-y-2" aria-label="Cadeia de projetos">
              {chain.map((entry, idx) => {
                const isCurrent = idx === chain.length - 1
                return (
                  <li
                    key={entry.id}
                    className={`flex gap-2 items-start text-xs ${isCurrent ? 'text-white' : 'text-gray-400'}`}
                    aria-current={isCurrent ? 'true' : undefined}
                  >
              <span aria-label={isCurrent ? 'Projeto atual' : 'Projeto anterior'} className="flex-shrink-0 mt-0.5">
                {isCurrent ? '📍' : '○'}
              </span>
                    <span>
                      <span className="font-semibold">Poste {entry.numero}</span>
                      <br />
                      <span className="opacity-70">Atualizado: {formatDate(entry.atualizado_em)}</span>
                      {entry.calculos_count > 0 && (
                        <span className="ml-1 opacity-70">• {entry.calculos_count} cálc.</span>
                      )}
                    </span>
                  </li>
                )
              })}
            </ol>
          )}
        </div>
      )}
    </div>
  )
}
