/* Tests for TelaProjetoInicial accessibility — items 9–13 of QA checklist */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import TelaProjetoInicial from '@/components/projeto/TelaProjetoInicial'

const baseDados = {
  orgao: '',
  ns: '',
  projeto: '',
  endereco: '',
  estudadoPor: '',
  matricula: '',
  data: '',
}

function renderTela(overrides = {}) {
  return render(
    <TelaProjetoInicial
      dados={baseDados}
      onChange={vi.fn()}
      onConfirm={vi.fn()}
      onGuestConfirm={vi.fn()}
      onBack={vi.fn()}
      loading={false}
      error={null}
      {...overrides}
    />
  )
}

describe('TelaProjetoInicial — accessibility', () => {
  it('Campo Projeto is present with label association via htmlFor', () => {
    renderTela()
    const input = screen.getByRole('textbox', { name: /projeto/i })
    expect(input).toBeInTheDocument()
    expect(input).toHaveAttribute('id', 'projeto')
    const label = document.querySelector('label[for="projeto"]')
    expect(label).toBeTruthy()
  })

  it('projeto input has aria-describedby pointing to the error element id', () => {
    renderTela()
    const input = screen.getByRole('textbox', { name: /projeto/i })
    expect(input).toHaveAttribute('aria-describedby', 'project-projeto-error')
  })

  it('no aria-invalid when there is no error', () => {
    renderTela({ error: null })
    const input = screen.getByRole('textbox', { name: /projeto/i })
    expect(input).not.toHaveAttribute('aria-invalid')
  })

  it('aria-invalid=true when error is present', () => {
    renderTela({ error: 'Projeto é obrigatório.' })
    const input = screen.getByRole('textbox', { name: /projeto/i })
    expect(input).toHaveAttribute('aria-invalid', 'true')
  })

  it('error message element is rendered with correct id', () => {
    renderTela({ error: 'Projeto é obrigatório.' })
    const errorEl = document.getElementById('project-projeto-error')
    expect(errorEl).toBeTruthy()
    expect(errorEl.textContent).toBe('Projeto é obrigatório.')
  })

  it('error message element is always in DOM (empty when no error)', () => {
    renderTela({ error: null })
    const errorEl = document.getElementById('project-projeto-error')
    expect(errorEl).toBeTruthy()
    expect(errorEl.textContent).toBe('')
  })

  it('Enter key submits the form', async () => {
    const onConfirm = vi.fn()
    renderTela({ onConfirm })
    const input = screen.getByRole('textbox', { name: /projeto/i })
    await userEvent.type(input, '{enter}')
    expect(onConfirm).toHaveBeenCalledTimes(1)
  })

  it('Iniciar cálculo button submits the form', async () => {
    const onConfirm = vi.fn()
    renderTela({ onConfirm })
    const btn = screen.getByRole('button', { name: /iniciar cálculo/i })
    await userEvent.click(btn)
    expect(onConfirm).toHaveBeenCalledTimes(1)
  })
})
