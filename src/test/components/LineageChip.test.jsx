/**
 * Tests for LineageChip component.
 *
 * - Renders nothing when origemId is null.
 * - Renders collapsed chip when origemId is set.
 * - Expands to show loading state.
 * - Expands to show error state.
 * - Expands to show ancestry chain.
 * - Collapses back on ✕ click.
 */
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'

import LineageChip from '@/components/projeto/LineageChip'

// Mock useLineage so tests are isolated from API
vi.mock('@/hooks/useLineage', () => ({
  useLineage: vi.fn(),
}))

import { useLineage } from '@/hooks/useLineage'

const CHAIN = [
  { id: 'a', numero: '7', tipo_poste: 'DT', modelo_poste: '9m', projeto_id: 'p1', atualizado_em: '2025-06-01T00:00:00Z', calculos_count: 3 },
  { id: 'b', numero: '7', tipo_poste: 'DT', modelo_poste: '9m', projeto_id: 'p2', atualizado_em: '2026-01-15T00:00:00Z', calculos_count: 1 },
]

describe('LineageChip', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders nothing when origemId is null', () => {
    useLineage.mockReturnValue({ chain: [], profundidade: 0, loading: false, error: '' })
    const { container } = render(<LineageChip posteId="b" origemId={null} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders collapsed chip when origemId is set', () => {
    useLineage.mockReturnValue({ chain: [], profundidade: 0, loading: false, error: '' })
    render(<LineageChip posteId="b" origemId="a" />)
    expect(screen.getByRole('button', { name: /ver linhagem/i })).toBeInTheDocument()
    expect(screen.getByText(/continuação/i)).toBeInTheDocument()
  })

  it('shows profundidade in chip when > 0', () => {
    useLineage.mockReturnValue({ chain: CHAIN, profundidade: 2, loading: false, error: '' })
    render(<LineageChip posteId="b" origemId="a" />)
    expect(screen.getByText('(2)')).toBeInTheDocument()
  })

  it('expands to show loading indicator', () => {
    useLineage.mockReturnValue({ chain: [], profundidade: 0, loading: true, error: '' })
    render(<LineageChip posteId="b" origemId="a" />)
    fireEvent.click(screen.getByRole('button', { name: /ver linhagem/i }))
    expect(screen.getByText(/carregando/i)).toBeInTheDocument()
  })

  it('expands to show error', () => {
    useLineage.mockReturnValue({ chain: [], profundidade: 0, loading: false, error: 'Falha de rede' })
    render(<LineageChip posteId="b" origemId="a" />)
    fireEvent.click(screen.getByRole('button', { name: /ver linhagem/i }))
    expect(screen.getByRole('alert')).toHaveTextContent('Falha de rede')
  })

  it('expands to show ancestry chain entries', () => {
    useLineage.mockReturnValue({ chain: CHAIN, profundidade: 2, loading: false, error: '' })
    render(<LineageChip posteId="b" origemId="a" />)
    fireEvent.click(screen.getByRole('button', { name: /ver linhagem/i }))
    expect(screen.getAllByText(/poste 7/i)).toHaveLength(2)
    expect(screen.getByRole('list')).toBeInTheDocument()
  })

  it('marks last entry as current', () => {
    useLineage.mockReturnValue({ chain: CHAIN, profundidade: 2, loading: false, error: '' })
    render(<LineageChip posteId="b" origemId="a" />)
    fireEvent.click(screen.getByRole('button', { name: /ver linhagem/i }))
    const items = screen.getAllByRole('listitem')
    expect(items[items.length - 1]).toHaveAttribute('aria-current', 'true')
  })

  it('collapses when ✕ is clicked', () => {
    useLineage.mockReturnValue({ chain: CHAIN, profundidade: 2, loading: false, error: '' })
    render(<LineageChip posteId="b" origemId="a" />)
    fireEvent.click(screen.getByRole('button', { name: /ver linhagem/i }))
    expect(screen.getByRole('region')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /fechar linhagem/i }))
    expect(screen.queryByRole('region')).not.toBeInTheDocument()
  })
})
