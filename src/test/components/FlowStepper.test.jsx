/* Tests for FlowStepper keyboard accessibility (FE-20) */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import FlowStepper from '@/components/fluxo/FlowStepper'

describe('FlowStepper — accessibility', () => {
  it('renders a <nav> landmark with aria-label', () => {
    render(<FlowStepper etapaAtual="projeto" />)
    const nav = screen.getByRole('navigation')
    expect(nav).toBeInTheDocument()
    expect(nav).toHaveAttribute('aria-label', expect.stringMatching(/fluxo/i))
  })

  it('renders an ordered list inside the stepper', () => {
    render(<FlowStepper etapaAtual="calculo" />)
    expect(screen.getByRole('list')).toBeInTheDocument()
  })

  it('all four step listitem elements are present', () => {
    render(<FlowStepper etapaAtual="ponto" />)
    const items = screen.getAllByRole('listitem')
    const stepLabels = items.map(el => el.getAttribute('aria-label') || '').filter(Boolean)
    expect(stepLabels.length).toBe(4)
  })

  it('active step has aria-current="step"', () => {
    render(<FlowStepper etapaAtual="calculo" resultado={{ mt1: {} }} />)
    const current = screen.getAllByRole('listitem').find(
      el => el.getAttribute('aria-current') === 'step'
    )
    expect(current).toBeTruthy()
    expect(current.getAttribute('aria-label')).toMatch(/cálculo/i)
  })

  it('done steps do NOT have aria-current', () => {
    render(<FlowStepper etapaAtual="calculo" />)
    const items = screen.getAllByRole('listitem').filter(el => el.getAttribute('aria-label'))
    const doneItems = items.filter(el =>
      el.getAttribute('aria-label')?.includes('concluída')
    )
    doneItems.forEach(el => {
      expect(el.getAttribute('aria-current')).toBeNull()
    })
  })

  it('"Próximo ponto" button appears only when persistencia is saved and onNextPonto is provided', () => {
    const onNext = vi.fn()
    render(
      <FlowStepper
        etapaAtual="persistido"
        statusPersistencia="saved"
        onNextPonto={onNext}
      />
    )
    const btn = screen.getByRole('button', { name: /próximo ponto/i })
    expect(btn).toBeInTheDocument()
  })

  it('"Próximo ponto" button is NOT shown when persistencia is not saved', () => {
    render(
      <FlowStepper
        etapaAtual="calculo"
        statusPersistencia="saving"
        onNextPonto={vi.fn()}
      />
    )
    expect(screen.queryByRole('button', { name: /próximo ponto/i })).not.toBeInTheDocument()
  })

  it('condensed mode renders nav landmark with aria-label', () => {
    render(<FlowStepper etapaAtual="calculo" condensed />)
    const nav = screen.getByRole('navigation')
    expect(nav).toBeInTheDocument()
  })

  it('condensed mode: current chip has aria-current="step"', () => {
    render(<FlowStepper etapaAtual="ponto" condensed />)
    const items = screen.getAllByRole('listitem')
    const currentItem = items.find(el => el.getAttribute('aria-current') === 'step')
    expect(currentItem).toBeTruthy()
    expect(currentItem.getAttribute('aria-label')).toMatch(/etapa atual/i)
  })
})
