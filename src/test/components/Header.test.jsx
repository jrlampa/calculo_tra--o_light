/* Tests for Header PersistenciaChip state contract (FE-21/22) */
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'

import Header from '@/components/header/Header'

const baseDados = {
  orgao: '',
  ns: '',
  projeto: 'Proj',
  ponto: '1',
  endereco: '',
  matricula: '',
  data: '',
  estudadoPor: '',
}

function renderHeader(overrides = {}) {
  return render(
    <Header
      dados={baseDados}
      onChange={vi.fn()}
      onConfirmPonto={vi.fn()}
      canConfirmPonto={false}
      {...overrides}
    />
  )
}

describe('PersistenciaChip — state contract', () => {
  it('saving → shows "Salvando..." and no retry CTA', () => {
    renderHeader({
      persistenciaStatus: 'saving',
      persistenciaMensagem: 'Salvando...',
    })
    const chip = document.getElementById('header-persistencia-status')
    expect(chip).toHaveTextContent('Salvando...')
    expect(screen.queryByRole('button', { name: /tentar novamente/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /reenviar/i })).not.toBeInTheDocument()
  })

  it('queued → shows countdown message and "Reenviar" CTA', async () => {
    const onRetry = vi.fn()
    renderHeader({
      persistenciaStatus: 'queued',
      persistenciaMensagem: 'Na fila. Tentando em 4s...',
      onRetryPersistencia: onRetry,
    })
    const chip = document.getElementById('header-persistencia-status')
    expect(chip).toHaveTextContent(/na fila/i)
    const reenviarBtn = screen.getByRole('button', { name: /reenviar/i })
    expect(reenviarBtn).toBeInTheDocument()
    await userEvent.click(reenviarBtn)
    expect(onRetry).toHaveBeenCalledTimes(1)
  })

  it('saved → shows "Salvo" and no retry CTA', () => {
    renderHeader({
      persistenciaStatus: 'saved',
      persistenciaMensagem: 'Salvo',
    })
    const chip = document.getElementById('header-persistencia-status')
    expect(chip).toHaveTextContent('Salvo')
    expect(screen.queryByRole('button', { name: /tentar novamente/i })).not.toBeInTheDocument()
  })

  it('error (transient, willRetry=true) → shows message and no manual CTA', () => {
    renderHeader({
      persistenciaStatus: 'error',
      persistenciaMensagem: 'Falha ao salvar: timeout',
      persistenciaWillRetry: true,
      persistenciaIsForbidden: false,
    })
    const chip = document.getElementById('header-persistencia-status')
    expect(chip).toHaveTextContent(/falha ao salvar/i)
    expect(screen.queryByRole('button', { name: /tentar novamente/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /reconfirmar/i })).not.toBeInTheDocument()
  })

  it('error (transient, willRetry=false) → shows "Tentar novamente" CTA', async () => {
    const onRetry = vi.fn()
    renderHeader({
      persistenciaStatus: 'error',
      persistenciaMensagem: 'Falha ao salvar.',
      persistenciaWillRetry: false,
      persistenciaIsForbidden: false,
      onRetryPersistencia: onRetry,
    })
    const btn = screen.getByRole('button', { name: /tentar novamente/i })
    expect(btn).toBeInTheDocument()
    await userEvent.click(btn)
    expect(onRetry).toHaveBeenCalledTimes(1)
  })

  it('error_permission (isForbidden=true) → shows "Reconfirmar projeto" CTA', async () => {
    const onReconfirm = vi.fn()
    renderHeader({
      persistenciaStatus: 'error',
      persistenciaMensagem: 'Acesso negado: verifique o proprietário do projeto.',
      persistenciaIsForbidden: true,
      onReconfirmProjeto: onReconfirm,
    })
    const chip = document.getElementById('header-persistencia-status')
    expect(chip).toHaveTextContent(/acesso negado/i)
    const btn = screen.getByRole('button', { name: /reconfirmar projeto/i })
    expect(btn).toBeInTheDocument()
    await userEvent.click(btn)
    expect(onReconfirm).toHaveBeenCalledTimes(1)
  })

  it('error_permission → no "Tentar novamente" CTA shown', () => {
    renderHeader({
      persistenciaStatus: 'error',
      persistenciaMensagem: 'Acesso negado.',
      persistenciaIsForbidden: true,
      onReconfirmProjeto: vi.fn(),
    })
    expect(screen.queryByRole('button', { name: /tentar novamente/i })).not.toBeInTheDocument()
  })

  it('VinculoChip and PersistenciaChip are independent role=status elements', () => {
    renderHeader({
      pontoStatus: 'idle',
      pontoMensagem: 'Aguardando ponto…',
      persistenciaStatus: 'saving',
      persistenciaMensagem: 'Salvando...',
    })
    const statusEls = screen.getAllByRole('status')
    expect(statusEls.length).toBeGreaterThanOrEqual(2)
    const ids = statusEls.map(el => el.id)
    expect(ids).toContain('header-vinculo-status')
    expect(ids).toContain('header-persistencia-status')
  })
})
