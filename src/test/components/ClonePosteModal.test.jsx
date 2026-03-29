/**
 * Tests for ClonePosteModal component.
 *
 * - Renders modal with project selector.
 * - Loads and displays projects (excluding current).
 * - Loads postes when a project is selected.
 * - Shows error when listProjetos fails.
 * - Clone button is disabled until a poste is selected.
 * - Calls onClone with the selected poste ID.
 * - Calls onClose when Cancelar is clicked.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'

import ClonePosteModal from '@/components/projeto/ClonePosteModal'

// Mock listPostes from calculoApi
vi.mock('@/services/calculoApi', () => ({
  listPostes: vi.fn(),
}))
import { listPostes } from '@/services/calculoApi'

const PROJETOS = [
  { id: 'p1', nome: 'Projeto Alfa', data_estudo: '01/01/2025', total_pontos: 3 },
  { id: 'p2', nome: 'Projeto Beta', data_estudo: '06/01/2025', total_pontos: 1 },
  { id: 'p-current', nome: 'Projeto Atual', data_estudo: '', total_pontos: 0 },
]

const POSTES = [
  { id: 'pt1', numero: '5', tipo_poste: 'DT', modelo_poste: '9m', origem_id: null },
  { id: 'pt2', numero: '6', tipo_poste: 'Concreto', modelo_poste: '11m', origem_id: null },
]

const listProjetos = vi.fn()

describe('ClonePosteModal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    listProjetos.mockResolvedValue(PROJETOS)
    listPostes.mockResolvedValue(POSTES)
  })

  it('renders dialog with title', async () => {
    render(
      <ClonePosteModal
        onClone={vi.fn()}
        onClose={vi.fn()}
        listProjetos={listProjetos}
        projetoAtualId="p-current"
      />
    )
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText(/clonar poste de outro projeto/i)).toBeInTheDocument()
  })

  it('excludes current project from list', async () => {
    render(
      <ClonePosteModal
        onClone={vi.fn()}
        onClose={vi.fn()}
        listProjetos={listProjetos}
        projetoAtualId="p-current"
      />
    )
    await waitFor(() => expect(screen.queryByText(/carregando projetos/i)).not.toBeInTheDocument())
    expect(screen.queryByText(/projeto atual/i)).not.toBeInTheDocument()
    expect(screen.getByText(/projeto alfa/i)).toBeInTheDocument()
  })

  it('loads postes when a project is selected', async () => {
    render(
      <ClonePosteModal
        onClone={vi.fn()}
        onClose={vi.fn()}
        listProjetos={listProjetos}
        projetoAtualId="p-current"
      />
    )
    await waitFor(() => screen.getByText(/projeto alfa/i))
    fireEvent.change(screen.getByLabelText(/projeto de origem/i), { target: { value: 'p1' } })
    await waitFor(() => expect(listPostes).toHaveBeenCalledWith('p1'))
    expect(await screen.findByText(/poste 5/i)).toBeInTheDocument()
  })

  it('clone button is disabled until a poste is selected', async () => {
    render(
      <ClonePosteModal
        onClone={vi.fn()}
        onClose={vi.fn()}
        listProjetos={listProjetos}
        projetoAtualId="p-current"
      />
    )
    await waitFor(() => screen.getByText(/projeto alfa/i))
    const btn = screen.getByRole('button', { name: /clonar/i })
    expect(btn).toBeDisabled()
  })

  it('calls onClone with selected poste id', async () => {
    const onClone = vi.fn().mockResolvedValue(undefined)
    const onClose = vi.fn()
    render(
      <ClonePosteModal
        onClone={onClone}
        onClose={onClose}
        listProjetos={listProjetos}
        projetoAtualId="p-current"
      />
    )
    await waitFor(() => screen.getByText(/projeto alfa/i))
    fireEvent.change(screen.getByLabelText(/projeto de origem/i), { target: { value: 'p1' } })
    await waitFor(() => screen.getByText(/poste 5/i))
    fireEvent.change(screen.getByLabelText(/poste a clonar/i), { target: { value: 'pt1' } })
    fireEvent.click(screen.getByRole('button', { name: /clonar/i }))
    await waitFor(() => expect(onClone).toHaveBeenCalledWith('pt1'))
    expect(onClose).toHaveBeenCalled()
  })

  it('calls onClose when Cancelar is clicked', async () => {
    const onClose = vi.fn()
    render(
      <ClonePosteModal
        onClone={vi.fn()}
        onClose={onClose}
        listProjetos={listProjetos}
        projetoAtualId="p-current"
      />
    )
    fireEvent.click(screen.getByRole('button', { name: /cancelar/i }))
    expect(onClose).toHaveBeenCalled()
  })

  it('shows error when listProjetos fails', async () => {
    listProjetos.mockRejectedValueOnce(new Error('Sem conexão'))
    render(
      <ClonePosteModal
        onClone={vi.fn()}
        onClose={vi.fn()}
        listProjetos={listProjetos}
        projetoAtualId="p-current"
      />
    )
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent(/sem conexão/i))
  })
})
