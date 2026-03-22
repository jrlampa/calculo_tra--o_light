import { test, expect } from '@playwright/test'

const PROJETO_ID = '11111111-1111-4111-8111-111111111111'
const PONTO_ID = '22222222-2222-4222-8222-222222222222'

const CONFIG_FIXTURE = {
  redes: ['Convencional', 'Compacta'],
  cabos: ['397MCM-CA, Nu', 'CAA 2 AWG'],
  postes: {
    'Concreto circular': ['11 m / 600 daN', '12 m / 1000 daN'],
    'Duplo T': ['11 m / 600 daN'],
  },
  cabos_por_rede: {
    Convencional: ['397MCM-CA, Nu'],
    Compacta: ['CAA 2 AWG'],
  },
}

const CALCULO_FIXTURE = {
  mt1: {
    tracao_dan: 150,
    angulo_graus: 0,
    texto: 'TRACAO MT 1 NIVEL (100 mm do topo): 150 daN 0°',
  },
  mt2: {
    tracao_dan: 0,
    angulo_graus: 0,
    texto: 'TRACAO MT 2 NIVEL (100 mm do topo): 0 daN 0°',
  },
  bt: {
    tracao_dan: 0,
    angulo_graus: 0,
    texto: 'TRACAO BT (100 mm do topo): 0 daN 0°',
  },
  btz: {
    tracao_dan: 0,
    angulo_graus: 0,
    texto: 'TRACAO RAMAIS BTZERO (100 mm do topo): 0 daN 0°',
  },
  ral: {
    tracao_dan: 0,
    angulo_graus: 0,
    texto: 'TRACAO RAMAIS DE LIGACAO (100 mm do topo): 0 daN 0°',
  },
  total_tracao_dan: 150,
  total_angulo_graus: 0,
  poste_ecc_dan: 0,
  texto_total: 'TRACAO TOTAL: 150 daN 0°',
  vetores: [{ angulo_graus: 0, tracao_dan: 150, label: 'MT1' }],
}

const jsonResponse = (route, status, body) => route.fulfill({
  status,
  contentType: 'application/json',
  body: JSON.stringify(body),
})

function secao(page, tituloParcial) {
  return page
    .locator('.sec-panel')
    .filter({ has: page.locator('.sec-title', { hasText: tituloParcial }) })
    .first()
}

async function mockConfigSuccess(page) {
  await page.route('**/api/config', async route => {
    if (route.request().method() !== 'GET') {
      await route.continue()
      return
    }

    await jsonResponse(route, 200, CONFIG_FIXTURE)
  })
}

async function mockProjetoCreation(page) {
  await page.route('**/api/projetos', async route => {
    if (route.request().method() !== 'POST') {
      await route.continue()
      return
    }

    const payload = route.request().postDataJSON() ?? {}
    await jsonResponse(route, 201, {
      id: PROJETO_ID,
      orgao: payload.orgao ?? '',
      ns: payload.ns ?? '',
      nome: payload.nome ?? 'Projeto E2E',
      endereco: payload.endereco ?? '',
      estudado_por: payload.estudado_por ?? '',
      matricula: payload.matricula ?? '',
      data_estudo: payload.data_estudo ?? '',
      total_pontos: 0,
    })
  })
}

async function mockCalculo(page, onRequest) {
  await page.route('**/api/calcular', async route => {
    if (route.request().method() !== 'POST') {
      await route.continue()
      return
    }

    if (typeof onRequest === 'function') {
      onRequest(route.request().postDataJSON() ?? null)
    }

    await jsonResponse(route, 200, CALCULO_FIXTURE)
  })
}

async function iniciarFluxoProjeto(page, nomeProjeto = 'Projeto fluxo critico E2E') {
  await page.addInitScript(() => { window.localStorage.setItem('guest_mode', 'true'); });
  await page.goto('/')
  await expect(page.getByRole('heading', { name: /Cadastro do projeto/i })).toBeVisible()

  await page.getByLabel('Projeto').fill(nomeProjeto)
  await page.getByRole('button', { name: /Confirmar e iniciar c.lculo/i }).click()

  await expect(page.locator('.btn-apaga')).toBeVisible()
}

test.describe('UI critica - checklist rapido e fluxo completo', () => {
  test('a11y: submit sem projeto marca campo, associa erro e mantem foco', async ({ page }) => {
    await mockConfigSuccess(page)

    await page.addInitScript(() => { window.localStorage.setItem('guest_mode', 'true'); });
    await page.goto('/')

    const projetoInput = page.getByLabel('Projeto')
    await expect(projetoInput).toBeFocused()

    await page.getByRole('button', { name: /Confirmar e iniciar c.lculo/i }).click()

    await expect(projetoInput).toHaveAttribute('aria-invalid', 'true')
    await expect(projetoInput).toHaveAttribute('aria-describedby', /project-projeto-error/)

    const erroId = await projetoInput.getAttribute('aria-describedby')
    await expect(page.locator(`#${erroId}`)).toContainText(/Informe o nome do projeto/i)
    await expect(projetoInput).toBeFocused()
  })

  test('fallback /api/config: erro inicial visivel e retry bem-sucedido', async ({ page }) => {
    let configAttempts = 0
    let shouldSucceedConfig = false

    await page.route('**/api/config', async route => {
      if (route.request().method() !== 'GET') {
        await route.continue()
        return
      }

      configAttempts += 1

      if (!shouldSucceedConfig) {
        await jsonResponse(route, 500, { detail: 'falha inicial simulada' })
        return
      }

      await jsonResponse(route, 200, CONFIG_FIXTURE)
    })

    await mockProjetoCreation(page)
    await mockCalculo(page)

    await iniciarFluxoProjeto(page, 'Projeto fallback config E2E')

    const bannerErroConfig = page.locator('.config-status-banner--error')
    await expect(bannerErroConfig).toBeVisible()
    await expect(bannerErroConfig).toContainText(/Falha ao carregar \/api\/config/i)

    shouldSucceedConfig = true
    await page.getByRole('button', { name: 'Tentar novamente' }).click()

    await expect.poll(() => configAttempts).toBeGreaterThanOrEqual(3)
    await expect(bannerErroConfig).toHaveCount(0)
    await expect(page.locator('.config-status-banner')).toHaveCount(0)
    await expect.poll(async () => {
      const tipoPosteOptions = await page.locator('.poste-select').first().evaluate(element => (
        Array.from(element.options).map(option => option.textContent?.trim() || '')
      ))

      return tipoPosteOptions.includes('Concreto circular')
    }).toBe(true)
  })

  test.skip('fluxo critico Projeto -> Ponto -> Calculo -> Persistencia', async ({ page }) => {
    let payloadCriacaoPonto = null
    let ultimoPayloadCalculo = null
    let payloadPersistido = null
    let persistCalls = 0

    await mockConfigSuccess(page)
    await mockProjetoCreation(page)
    await mockCalculo(page, payload => {
      ultimoPayloadCalculo = payload
    })

    await page.route('**/api/projetos/*/pontos', async route => {
      if (route.request().method() !== 'POST') {
        await route.continue()
        return
      }

      payloadCriacaoPonto = route.request().postDataJSON() ?? null

      await jsonResponse(route, 201, {
        id: PONTO_ID,
        projeto_id: PROJETO_ID,
        ponto: payloadCriacaoPonto?.ponto ?? 'P1',
        tipo_poste: payloadCriacaoPonto?.tipo_poste ?? '',
        modelo_poste: payloadCriacaoPonto?.modelo_poste ?? '',
      })
    })

    await page.route('**/api/pontos/*/calculo', async route => {
      if (route.request().method() !== 'POST') {
        await route.continue()
        return
      }

      payloadPersistido = route.request().postDataJSON() ?? null
      persistCalls += 1
      await jsonResponse(route, 201, { success: true })
    })

    await iniciarFluxoProjeto(page)

    await page.getByLabel('Ponto').fill('P1')
    await page.locator('.poste-select').first().selectOption({ label: 'Concreto circular' })
    await page.locator('.poste-select').nth(1).selectOption({ label: '11 m / 600 daN' })
    await page.locator('.header-action-button').click()

    // Novo seletor: vinculo-chip
    await expect(page.locator('.vinculo-chip')).toContainText(/Ponto\s+P1\s+confirmado|Ponto\s+confirmado/i)
    expect(payloadCriacaoPonto).toMatchObject({
      ponto: 'P1',
      tipo_poste: 'Concreto circular',
      modelo_poste: '11 m / 600 daN',
    })

    const secaoMt1 = secao(page, 'MT - 1')
    await secaoMt1.locator('select[id="tipoRede-t1"]').selectOption({ label: 'Convencional' })
    await secaoMt1.locator('select[id="tipoCabo-t1"]').selectOption({ label: '397MCM-CA, Nu' })
    await secaoMt1.locator('input[id="vao-t1"]').fill('50')
    await secaoMt1.locator('input[id="flecha-t1"]').fill('1,5')
    await secaoMt1.locator('input[id="angulo-t1"]').fill('0')
    await secaoMt1.locator('input[id="alturaPoste-t1"]').fill('11')
    await secaoMt1.locator('input[id="alturaAncoragem-t1"]').fill('1')

    await expect.poll(() => persistCalls, { timeout: 15_000 }).toBeGreaterThan(0)

    expect(payloadPersistido).toBeTruthy()
    expect(payloadPersistido.ponto_id).toBe(PONTO_ID)
    expect(Array.isArray(payloadPersistido.niveis)).toBeTruthy()
    expect(payloadPersistido.niveis).toHaveLength(5)

    const niveis = payloadPersistido.niveis.map(item => item.nivel)
    expect(niveis).toEqual(['MT1', 'MT2', 'BT', 'BTZ', 'RAL'])

    // Novo seletor: persistencia-chip
    await expect(page.locator('.persistencia-chip')).toContainText(/Cálculo salvo|Salvo/i, { timeout: 15_000 })
  })

  test.skip('persistencia: erro 403 forbidden bloqueia auto-retry', async ({ page }) => {
    let persistCalls = 0

    await mockConfigSuccess(page)
    await mockProjetoCreation(page)
    await mockCalculo(page)

    await page.route('**/api/projetos/*/pontos', async route => {
      if (route.request().method() !== 'POST') {
        await route.continue()
        return
      }

      const payloadCriacaoPonto = route.request().postDataJSON() ?? {}
      await jsonResponse(route, 201, {
        id: PONTO_ID,
        projeto_id: PROJETO_ID,
        ponto: payloadCriacaoPonto?.ponto ?? 'P2-Forbidden',
        tipo_poste: payloadCriacaoPonto?.tipo_poste ?? '',
        modelo_poste: payloadCriacaoPonto?.modelo_poste ?? '',
      })
    })

    await page.route('**/api/pontos/*/calculo', async route => {
      if (route.request().method() !== 'POST') {
        await route.continue()
        return
      }

      persistCalls += 1
      // Simular erro 403: Forbidden (sem permissão para persistir neste ponto)
      await jsonResponse(route, 403, {
        detail: 'Você não tem permissão para persistir dados neste ponto.',
      })
    })

    await iniciarFluxoProjeto(page)

    await page.getByLabel('Ponto').fill('P2-Forbidden')
    await page.locator('.poste-select').first().selectOption({ label: 'Concreto circular' })
    await page.locator('.poste-select').nth(1).selectOption({ label: '11 m / 600 daN' })
    await page.locator('.header-action-button').click()

    await expect(page.locator('.vinculo-chip')).toContainText(/Ponto\s+.*confirmado/i)

    // Preencher MT1 para disparar persistência
    const secaoMt1 = secao(page, 'MT - 1')
    await secaoMt1.locator('select[id="tipoRede-t1"]').selectOption({ label: 'Convencional' })
    await secaoMt1.locator('select[id="tipoCabo-t1"]').selectOption({ label: '397MCM-CA, Nu' })
    await secaoMt1.locator('input[id="vao-t1"]').fill('50')

    // Aguardar primeira tentativa de persistência
    await expect.poll(() => persistCalls, { timeout: 15_000 }).toBeGreaterThanOrEqual(1)

    // Verificar que erro 403 é exibido E nenhuma retentativa automática ocorre
    await expect(page.locator('.persistencia-chip')).toContainText(/negar|acesso negado|permission/i, {
      timeout: 5_000,
    })

    const callsApos1s = persistCalls
    await page.waitForTimeout(2000)
    // Nenhuma retentativa automática deve ocorrer após erro 403
    expect(persistCalls).toBe(callsApos1s)
  })
})