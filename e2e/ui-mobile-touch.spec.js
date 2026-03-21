import { test, expect, devices } from '@playwright/test'

const PROJETO_ID = '33333333-3333-4333-8333-333333333333'

const CONFIG_FIXTURE = {
  redes: ['Convencional'],
  cabos: ['397MCM-CA, Nu'],
  postes: {
    'Concreto circular': ['11 m / 600 daN'],
  },
  cabos_por_rede: {
    Convencional: ['397MCM-CA, Nu'],
  },
}

const CALCULO_FIXTURE = {
  mt1: { tracao_dan: 10, angulo_graus: 0, texto: 'TRACAO MT 1 NIVEL: 10 daN 0°' },
  mt2: { tracao_dan: 0, angulo_graus: 0, texto: 'TRACAO MT 2 NIVEL: 0 daN 0°' },
  bt: { tracao_dan: 0, angulo_graus: 0, texto: 'TRACAO BT: 0 daN 0°' },
  btz: { tracao_dan: 0, angulo_graus: 0, texto: 'TRACAO BTZERO: 0 daN 0°' },
  ral: { tracao_dan: 0, angulo_graus: 0, texto: 'TRACAO RAL: 0 daN 0°' },
  total_tracao_dan: 10,
  total_angulo_graus: 0,
  poste_ecc_dan: 0,
  texto_total: 'TRACAO TOTAL: 10 daN 0°',
  vetores: [{ angulo_graus: 0, tracao_dan: 10, label: 'MT1' }],
}

const jsonResponse = (route, status, body) => route.fulfill({
  status,
  contentType: 'application/json',
  body: JSON.stringify(body),
})

async function mockApiForMobile(page) {
  await page.route('**/api/config', async route => {
    if (route.request().method() !== 'GET') {
      await route.continue()
      return
    }

    await jsonResponse(route, 200, CONFIG_FIXTURE)
  })

  await page.route('**/api/projetos', async route => {
    if (route.request().method() !== 'POST') {
      await route.continue()
      return
    }

    const payload = route.request().postDataJSON() ?? {}
    await jsonResponse(route, 201, {
      id: PROJETO_ID,
      nome: payload.nome ?? 'Projeto Mobile',
    })
  })

  await page.route('**/api/calcular', async route => {
    if (route.request().method() !== 'POST') {
      await route.continue()
      return
    }

    await jsonResponse(route, 200, CALCULO_FIXTURE)
  })
}

async function alturaEfetiva(locator) {
  return locator.evaluate(element => {
    const bounds = element.getBoundingClientRect()
    return Math.round(bounds.height)
  })
}

async function iniciarEtapaCalculo(page) {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: /Cadastro do projeto/i })).toBeVisible()

  await page.getByLabel('Projeto').fill('Projeto touch mobile E2E')
  await page.getByRole('button', { name: /Confirmar e iniciar c.lculo/i }).click()

  await expect(page.locator('.btn-apaga')).toBeVisible()
}

test.describe('UI mobile touch - alvos e reflow', () => {
  test.use({
    viewport: devices['Pixel 5'].viewport,
    userAgent: devices['Pixel 5'].userAgent,
    deviceScaleFactor: devices['Pixel 5'].deviceScaleFactor,
    isMobile: true,
    hasTouch: true,
  })

  test('valida ambiente touch/coarse e altura minima dos alvos principais', async ({ page }) => {
    await mockApiForMobile(page)
    await page.goto('/')

    const pointerInfo = await page.evaluate(() => ({
      coarse: window.matchMedia('(pointer: coarse)').matches,
      anyCoarse: window.matchMedia('(any-pointer: coarse)').matches,
      maxTouchPoints: navigator.maxTouchPoints,
    }))

    expect(pointerInfo.maxTouchPoints).toBeGreaterThan(0)
    expect(pointerInfo.coarse || pointerInfo.anyCoarse).toBeTruthy()
    await expect(page.locator('.project-submit')).toBeVisible()
    await expect(await alturaEfetiva(page.locator('.project-submit'))).toBeGreaterThanOrEqual(44)

    await page.getByLabel('Projeto').fill('Projeto targets touch E2E')
    await page.getByRole('button', { name: /Confirmar e iniciar c.lculo/i }).click()

    const headerAction = page.locator('.header-action-button')
    const botaoApaga = page.locator('.btn-apaga')
    const seletorPoste = page.locator('.poste-select').first()

    await expect(headerAction).toBeVisible()
    await expect(botaoApaga).toBeVisible()
    await expect(seletorPoste).toBeVisible()

    await expect(await alturaEfetiva(headerAction)).toBeGreaterThanOrEqual(44)
    await expect(await alturaEfetiva(botaoApaga)).toBeGreaterThanOrEqual(44)
    await expect(await alturaEfetiva(seletorPoste)).toBeGreaterThanOrEqual(44)
  })

  test('valida reflow responsivo mobile com layout em coluna', async ({ page }) => {
    await mockApiForMobile(page)
    await iniciarEtapaCalculo(page)

    const direcaoLayout = await page.locator('.calc-layout').evaluate(element => getComputedStyle(element).flexDirection)
    expect(direcaoLayout).toBe('column')

    const colunaPrincipal = await page.locator('.calc-main-column').boundingBox()
    const colunaLateral = await page.locator('.calc-side-column').boundingBox()

    expect(colunaPrincipal).not.toBeNull()
    expect(colunaLateral).not.toBeNull()
    expect(colunaLateral.y).toBeGreaterThan(colunaPrincipal.y)
  })
})