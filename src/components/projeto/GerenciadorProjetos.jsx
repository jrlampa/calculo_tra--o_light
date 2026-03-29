/* This code snippet is a React functional component called `GerenciadorProjetos` that serves as a
project manager interface. Here's a breakdown of what the code is doing: */
import React, { useState, useEffect } from 'react'

export default function GerenciadorProjetos({ onNovo, onAbrir, onEditar, onExcluir, listProjetos, onClonarPoste }) {
  const [projetos, setProjetos] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [confirmDelete, setConfirmDelete] = useState(null) // { id, nome }
  const [deleteError, setDeleteError] = useState('')

  const fetchProjetos = async () => {
    setLoading(true)
    try {
      const data = await listProjetos()
      setProjetos(data)
      setError('')
    } catch (err) {
      setError(err.message || 'Erro ao carregar projetos. Verifique a conexão.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProjetos()
  }, [])

  const handleDeleteCancel = () => {
    setConfirmDelete(null)
    setDeleteError('')
  }

  const handleDeleteConfirm = async () => {
    if (!confirmDelete) {return}
    try {
      await onExcluir(confirmDelete.id)
      setConfirmDelete(null)
      setDeleteError('')
      await fetchProjetos()
    } catch (err) {
      setDeleteError(err.message || 'Erro ao excluir projeto.')
    }
  }

  return (
    <section className="project-screen">
      <div className="project-card max-w-4xl">
        <div className="project-heading flex justify-between items-center mb-6">
          <div>
            <span className="project-kicker">Dashboard</span>
            <h1 className="project-title">Meus Projetos</h1>
          </div>
          <div className="flex gap-2">
            {onClonarPoste && (
              <button
                onClick={onClonarPoste}
                className="project-submit px-4 py-2 h-auto text-sm bg-blue-800 hover:bg-blue-700 border-blue-600"
                title="Clonar um poste de outro projeto para um novo projeto"
              >
                🔀 Clonar Poste
              </button>
            )}
            <button 
              onClick={onNovo}
              className="project-submit px-6 py-2 h-auto text-sm"
            >
              + NOVO PROJETO
            </button>
          </div>
        </div>

        {error && <div className="project-error mb-4">{error}</div>}

        {loading ? (
          <div className="flex justify-center py-10">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : projetos.length === 0 ? (
          <div className="text-center py-12 border-2 border-dashed border-gray-700 rounded-lg">
            <p className="text-gray-400">Nenhum projeto encontrado.</p>
            <button onClick={onNovo} className="mt-4 text-blue-400 hover:underline">
              Crie seu primeiro projeto aqui
            </button>
          </div>
        ) : (
          <div className="grid gap-4">
            {projetos.map(proj => (
              <div key={proj.id} className="bg-gray-800/50 p-4 rounded-lg border border-gray-700 hover:border-gray-500 transition-all flex justify-between items-center">
                <div className="flex-1 cursor-pointer" onClick={() => onAbrir(proj)}>
                  <h3 className="font-bold text-lg text-white">{proj.nome}</h3>
                  <p className="text-sm text-gray-400">
                    {proj.data_estudo ? `Data: ${proj.data_estudo}` : 'Sem data registrada'} • {proj.total_pontos || 0} pontos
                  </p>
                </div>
                <div className="flex gap-2">
                  <button 
                    onClick={() => onAbrir(proj)}
                    className="p-2 hover:bg-green-900/30 text-green-400 rounded transition-colors"
                    title="Abrir Projeto"
                  >
                    📂 Abrir
                  </button>
                  <button 
                    onClick={() => onEditar(proj)}
                    className="p-2 hover:bg-blue-900/30 text-blue-400 rounded transition-colors"
                    title="Editar Cabeçalho"
                  >
                    ✏️ Editar
                  </button>
                  <button 
                    onClick={() => setConfirmDelete({ id: proj.id, nome: proj.nome })}
                    className="p-2 hover:bg-red-900/30 text-red-400 rounded transition-colors"
                    title="Excluir Projeto"
                  >
                    🗑️ Excluir
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Confirm Delete Dialog */}
      {confirmDelete && (
        <div
          role="alertdialog"
          aria-modal="true"
          aria-labelledby="confirm-delete-title"
          aria-describedby="confirm-delete-desc"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
        >
          <div className="bg-gray-900 border border-gray-700 rounded-xl shadow-2xl p-6 max-w-sm w-full mx-4">
            <h2 id="confirm-delete-title" className="text-lg font-bold text-white mb-2">
              Excluir Projeto
            </h2>
            <p id="confirm-delete-desc" className="text-gray-300 text-sm mb-4">
              Tem certeza que deseja excluir o projeto{' '}
              <strong className="text-white">&ldquo;{confirmDelete.nome}&rdquo;</strong>?
              Esta ação não pode ser desfeita.
            </p>
            {deleteError && (
              <p className="text-red-400 text-sm mb-3" role="alert">{deleteError}</p>
            )}
            <div className="flex justify-end gap-3">
              <button
                onClick={handleDeleteCancel}
                className="px-4 py-2 rounded-lg text-sm text-gray-300 hover:bg-gray-700 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleDeleteConfirm}
                className="px-4 py-2 rounded-lg text-sm font-semibold bg-red-700 hover:bg-red-600 text-white transition-colors"
              >
                Excluir
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}
