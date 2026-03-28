/**
 * ClonePosteModal — "Clonar poste de outro projeto"
 *
 * Workflow:
 *  1. User picks a source project from the list (excludes the current project).
 *  2. The modal loads the source project's postes.
 *  3. User picks one poste.
 *  4. Confirms: calls `onClone(posteOrigemId)` which delegates to
 *     `usePontoState.handleClonarDeOutroProjeto`.
 *
 * Props:
 *  - onClone(posteOrigemId)  Async handler; receives the source Poste UUID.
 *  - onClose()               Close without cloning.
 *  - listProjetos            API function to list all projects.
 *  - projetoAtualId          UUID of the currently open project (excluded).
 */
import React, { useState, useEffect, useCallback } from 'react'
import { listPostes } from '../../services/calculoApi.js'

export default function ClonePosteModal({ onClone, onClose, listProjetos, projetoAtualId }) {
  const [projetos, setProjetos] = useState([])
  const [projetoSelecionadoId, setProjetoSelecionadoId] = useState('')
  const [postes, setPostes] = useState([])
  const [posteSelecionadoId, setPosteSelecionadoId] = useState('')
  const [loadingProjetos, setLoadingProjetos] = useState(true)
  const [loadingPostes, setLoadingPostes] = useState(false)
  const [cloning, setCloning] = useState(false)
  const [error, setError] = useState('')

  // Load project list on mount
  useEffect(() => {
    const fetch = async () => {
      setLoadingProjetos(true)
      try {
        const data = await listProjetos(100, 0)
        // Exclude the currently open project
        setProjetos((data || []).filter(p => p.id !== projetoAtualId))
      } catch (err) {
        setError('Erro ao carregar projetos: ' + (err.message || 'Tente novamente.'))
      } finally {
        setLoadingProjetos(false)
      }
    }
    fetch()
  }, [listProjetos, projetoAtualId])

  // Load postes when a project is selected
  useEffect(() => {
    if (!projetoSelecionadoId) {
      setPostes([])
      setPosteSelecionadoId('')
      return
    }
    const fetch = async () => {
      setLoadingPostes(true)
      setPosteSelecionadoId('')
      setError('')
      try {
        const data = await listPostes(projetoSelecionadoId)
        setPostes(data || [])
      } catch (err) {
        setError('Erro ao carregar postes: ' + (err.message || 'Tente novamente.'))
        setPostes([])
      } finally {
        setLoadingPostes(false)
      }
    }
    fetch()
  }, [projetoSelecionadoId])

  const handleConfirm = useCallback(async () => {
    if (!posteSelecionadoId) return
    setCloning(true)
    setError('')
    try {
      await onClone(posteSelecionadoId)
      onClose()
    } catch (err) {
      setError('Erro ao clonar poste: ' + (err.message || 'Tente novamente.'))
    } finally {
      setCloning(false)
    }
  }, [posteSelecionadoId, onClone, onClose])

  const canConfirm = Boolean(posteSelecionadoId) && !cloning

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="clone-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
    >
      <div className="bg-gray-900 border border-gray-700 rounded-xl shadow-2xl p-6 max-w-md w-full mx-4">
        <h2 id="clone-modal-title" className="text-lg font-bold text-white mb-1">
          🔀 Clonar Poste de Outro Projeto
        </h2>
        <p className="text-sm text-gray-400 mb-4">
          Selecione o projeto de origem e o poste a clonar. O clone herda toda a
          configuração (níveis e travessias) e fica vinculado ao poste original
          para rastreabilidade.
        </p>

        {error && (
          <p className="text-red-400 text-sm mb-3" role="alert">{error}</p>
        )}

        {/* Project selector */}
        <div className="mb-4">
          <label htmlFor="clone-projeto-select" className="block text-sm font-semibold text-gray-300 mb-1">
            Projeto de origem
          </label>
          {loadingProjetos ? (
            <p className="text-gray-400 text-sm">Carregando projetos…</p>
          ) : projetos.length === 0 ? (
            <p className="text-gray-500 text-sm">Nenhum outro projeto disponível.</p>
          ) : (
            <select
              id="clone-projeto-select"
              className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={projetoSelecionadoId}
              onChange={e => setProjetoSelecionadoId(e.target.value)}
            >
              <option value="">Selecione um projeto…</option>
              {projetos.map(p => (
                <option key={p.id} value={p.id}>
                  {p.nome} {p.data_estudo ? `(${p.data_estudo})` : ''}
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Poste selector */}
        <div className="mb-5">
          <label htmlFor="clone-poste-select" className="block text-sm font-semibold text-gray-300 mb-1">
            Poste a clonar
          </label>
          {loadingPostes ? (
            <p className="text-gray-400 text-sm">Carregando postes…</p>
          ) : !projetoSelecionadoId ? (
            <p className="text-gray-500 text-sm">Selecione um projeto primeiro.</p>
          ) : postes.length === 0 ? (
            <p className="text-gray-500 text-sm">Nenhum poste encontrado neste projeto.</p>
          ) : (
            <select
              id="clone-poste-select"
              className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={posteSelecionadoId}
              onChange={e => setPosteSelecionadoId(e.target.value)}
            >
              <option value="">Selecione um poste…</option>
              {postes.map(p => (
                <option key={p.id} value={p.id}>
                  Poste {p.numero} — {p.tipo_poste} {p.modelo_poste}
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            disabled={cloning}
            className="px-4 py-2 rounded-lg text-sm text-gray-300 hover:bg-gray-700 transition-colors disabled:opacity-50"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            disabled={!canConfirm}
            aria-disabled={!canConfirm}
            className="px-4 py-2 rounded-lg text-sm font-semibold bg-blue-700 hover:bg-blue-600 text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {cloning ? 'Clonando…' : '🔀 Clonar'}
          </button>
        </div>
      </div>
    </div>
  )
}
