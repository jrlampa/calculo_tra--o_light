/**
 * Tests for MobileActionBar component.
 *
 * Covered paths:
 *  1. Confirm button always renders (all three layouts: desktop, tablet, mobile).
 *  2. Retry button visible only when canRetry=true.
 *  3. Next-point button visible only when canNextPoint=true.
 *  4. Confirm button disabled when statusPersistencia='saving'.
 *  5. Confirm button disabled when isDisabled=true.
 *  6. Confirm button enabled when statusPersistencia='idle'.
 *  7. onConfirm called when confirm button clicked.
 *  8. onRetry called when retry button clicked.
 *  9. onNextPoint called when next-point button clicked.
 * 10. Aria-labels present for accessibility.
 * 11. All three layout containers present in DOM (desktop, tablet, mobile).
 */
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'

import MobileActionBar from '@/components/actionBar/MobileActionBar'

// ─── helpers ──────────────────────────────────────────────────────────────────

function renderBar(props = {}) {
  return render(
    <MobileActionBar
      onConfirm={vi.fn()}
      onRetry={vi.fn()}
      onNextPoint={vi.fn()}
      {...props}
    />
  )
}

// ─── tests ────────────────────────────────────────────────────────────────────

describe('MobileActionBar', () => {
  // 1. Confirm button always rendered (3 layouts)
  it('renders confirm buttons (one per layout)', () => {
    renderBar()
    const confirmBtns = screen.getAllByRole('button', { name: /confirmar cálculo/i })
    // desktop + tablet + mobile = 3 confirm buttons
    expect(confirmBtns.length).toBe(3)
  })

  // 2. Retry button not rendered by default
  it('does not render retry button when canRetry=false', () => {
    renderBar({ canRetry: false })
    expect(screen.queryByRole('button', { name: /reenviar cálculo/i })).not.toBeInTheDocument()
  })

  it('renders retry buttons when canRetry=true', () => {
    renderBar({ canRetry: true })
    const retryBtns = screen.getAllByRole('button', { name: /reenviar cálculo/i })
    expect(retryBtns.length).toBeGreaterThan(0)
  })

  // 3. Next-point button
  it('does not render next-point button when canNextPoint=false', () => {
    renderBar({ canNextPoint: false })
    expect(screen.queryByRole('button', { name: /próximo ponto/i })).not.toBeInTheDocument()
  })

  it('renders next-point buttons when canNextPoint=true', () => {
    renderBar({ canNextPoint: true })
    const nextBtns = screen.getAllByRole('button', { name: /próximo ponto/i })
    expect(nextBtns.length).toBeGreaterThan(0)
  })

  // 4. Disabled when saving
  it('disables all confirm buttons when statusPersistencia=saving', () => {
    renderBar({ statusPersistencia: 'saving' })
    const confirmBtns = screen.getAllByRole('button', { name: /confirmar cálculo/i })
    confirmBtns.forEach(btn => expect(btn).toBeDisabled())
  })

  // 5. Disabled when isDisabled=true
  it('disables all confirm buttons when isDisabled=true', () => {
    renderBar({ isDisabled: true })
    const confirmBtns = screen.getAllByRole('button', { name: /confirmar cálculo/i })
    confirmBtns.forEach(btn => expect(btn).toBeDisabled())
  })

  // 6. Enabled when idle
  it('enables confirm buttons when statusPersistencia=idle', () => {
    renderBar({ statusPersistencia: 'idle' })
    const confirmBtns = screen.getAllByRole('button', { name: /confirmar cálculo/i })
    confirmBtns.forEach(btn => expect(btn).toBeEnabled())
  })

  // 7. onConfirm callback
  it('calls onConfirm when first confirm button is clicked', () => {
    const onConfirm = vi.fn()
    renderBar({ onConfirm })
    const confirmBtns = screen.getAllByRole('button', { name: /confirmar cálculo/i })
    fireEvent.click(confirmBtns[0])
    expect(onConfirm).toHaveBeenCalledTimes(1)
  })

  // 8. onRetry callback
  it('calls onRetry when retry button is clicked', () => {
    const onRetry = vi.fn()
    renderBar({ canRetry: true, onRetry })
    const retryBtn = screen.getAllByRole('button', { name: /reenviar cálculo/i })[0]
    fireEvent.click(retryBtn)
    expect(onRetry).toHaveBeenCalledTimes(1)
  })

  // 9. onNextPoint callback
  it('calls onNextPoint when next-point button is clicked', () => {
    const onNextPoint = vi.fn()
    renderBar({ canNextPoint: true, onNextPoint })
    const nextBtn = screen.getAllByRole('button', { name: /próximo ponto/i })[0]
    fireEvent.click(nextBtn)
    expect(onNextPoint).toHaveBeenCalledTimes(1)
  })

  // 10. Aria-labels for accessibility
  it('all confirm buttons have aria-label', () => {
    renderBar()
    const confirmBtns = screen.getAllByRole('button', { name: /confirmar cálculo/i })
    confirmBtns.forEach(btn => {
      expect(btn).toHaveAttribute('aria-label')
    })
  })

  // 11. Three layout containers present
  it('renders desktop, tablet and mobile containers in the DOM', () => {
    renderBar()
    expect(screen.getByTestId('action-bar-desktop')).toBeInTheDocument()
    expect(screen.getByTestId('action-bar-tablet')).toBeInTheDocument()
    expect(screen.getByTestId('action-bar-mobile')).toBeInTheDocument()
  })

  // 12. Disabled retry/next buttons when saving
  it('disables retry and next buttons when saving', () => {
    renderBar({ canRetry: true, canNextPoint: true, statusPersistencia: 'saving' })
    screen.getAllByRole('button', { name: /reenviar cálculo/i })
      .forEach(btn => expect(btn).toBeDisabled())
    screen.getAllByRole('button', { name: /próximo ponto/i })
      .forEach(btn => expect(btn).toBeDisabled())
  })
})
