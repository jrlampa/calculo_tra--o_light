/* Tests for the UndoToast component */
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'

import UndoToast from '@/components/ui/UndoToast'

describe('UndoToast', () => {
  it('renders nothing when clearState is idle', () => {
    const { container } = render(<UndoToast clearState="idle" countdown={0} onUndo={() => {}} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders undo_pending toast with countdown and Desfazer button', () => {
    render(<UndoToast clearState="undo_pending" countdown={4} onUndo={() => {}} />)
    expect(screen.getByText(/serão apagados em 4s/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /desfazer/i })).toBeInTheDocument()
  })

  it('calls onUndo when Desfazer is clicked', () => {
    const onUndo = vi.fn()
    render(<UndoToast clearState="undo_pending" countdown={3} onUndo={onUndo} />)
    fireEvent.click(screen.getByRole('button', { name: /desfazer/i }))
    expect(onUndo).toHaveBeenCalledTimes(1)
  })

  it('does not render Desfazer button when committed', () => {
    render(<UndoToast clearState="committed" countdown={0} onUndo={() => {}} />)
    expect(screen.queryByRole('button', { name: /desfazer/i })).not.toBeInTheDocument()
    expect(screen.getByText(/técnicos apagados/i)).toBeInTheDocument()
  })

  it('shows restoration message when undone', () => {
    render(<UndoToast clearState="undone" countdown={0} onUndo={() => {}} />)
    expect(screen.getByText(/dados restaurados/i)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /desfazer/i })).not.toBeInTheDocument()
  })

  it('has alert role for accessibility', () => {
    render(<UndoToast clearState="undo_pending" countdown={5} onUndo={() => {}} />)
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })
})
