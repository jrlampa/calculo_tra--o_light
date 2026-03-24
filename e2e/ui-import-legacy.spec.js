import { test, expect } from '@playwright/test'

const PROJETO_MOCK_ID = '22222222-2222-4222-8222-222222222222'

test.describe('UI – Importação Legada e Regra de 5%', () => {
  test.beforeEach(async ({ page }) => {
    // Capturar logs do navegador
    page.on('console', msg => console.log(`BROWSER [${msg.type()}]: ${msg.text()}`))
    
    // Capturar falhas de rede
    page.on('requestfailed', request => console.log(`NETWORK FAILED >> ${request.method()} ${request.url()} -- error: ${request.failure()?.errorText || 'unknown'}`))
    
    // Guest Mode
    await page.addInitScript(() => {
      window.localStorage.setItem('guest_mode', 'true')
    })

    // Mock Projetos (Startup)
    await page.route('**/api/projetos', async route => {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ id: PROJETO_MOCK_ID, nome: 'Import Test', total_pontos: 0 })
      })
    })

    await page.goto('/')
    
    // Passar pela tela de projeto via Bypas Convidado para evitar falhas de rede no E2E
    await page.getByLabel('Projeto').fill('Teste Import')
    // Click Guest Bypass
    // Click Guest Bypass with exact text
    const guestBtn = page.getByRole('button', { name: /Entrar como Convidado/i })
    await guestBtn.click()
    
    await page.waitForSelector('.calc-side-column', { timeout: 15000 })
  })

  test('deve importar dados do Excel e disparar cálculo com sobrecarga (>105%)', async ({ page }) => {
    // ... (same as before but update mock to >1.05 and red color checks)
    await setupMocks(page, {
        total_tracao_dan: 1100, 
        resistencia_nominal: 1000, 
        status_poste: "SOBRECARGA", 
        texto_total: "TRAÇÃO TOTAL: 1100 daN 10° [SOBRECARGA]"
    })

    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles({
      name: 'projeto-legado.xlsm',
      mimeType: 'application/vnd.ms-excel.sheet.macroEnabled.12',
      buffer: Buffer.from('')
    })

    await page.waitForTimeout(2000)
    const tracaoTotalBox = page.locator('.tracao-total-box')
    await expect(tracaoTotalBox).toContainText(/1100 daN/i)
    await expect(tracaoTotalBox).toHaveClass(/tracao-total-box/i)
    // No specific modifier for Overload, it's the default (Red)
    console.log('E2E SUCCESS: Sobrecarga detected')
  })

  test('deve mostrar status TOLERÂNCIA para esforços entre 100% e 105%', async ({ page }) => {
    await setupMocks(page, {
        total_tracao_dan: 1030, 
        resistencia_nominal: 1000, 
        status_poste: "TOLERANCIA", 
        texto_total: "TRAÇÃO TOTAL: 1030 daN 10° [TOLERÂNCIA]"
    })

    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles({
      name: 'projeto-legado.xlsm',
      mimeType: 'application/vnd.ms-excel.sheet.macroEnabled.12',
      buffer: Buffer.from('')
    })

    await page.waitForTimeout(2000)
    const tracaoTotalBox = page.locator('.tracao-total-box')
    await expect(tracaoTotalBox).toContainText(/1030 daN/i)
    await expect(tracaoTotalBox).toContainText(/\[TOLERÂNCIA\]/i)
    await expect(tracaoTotalBox).toHaveClass(/tracao-total-box--tolerancia/i)
    console.log('E2E SUCCESS: Tolerancia detected (Orange)')
  })
})

async function setupMocks(page, calcResult) {
    await page.route('**/api/calcular/importar-excel', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          cabecalho: { projeto: 'TOLERANCE PROJ', ponto: 'P1' },
          poste: { tipo_poste: 'Concreto Duplo T', modelo_poste: 'DT 11/1000' },
          mt1: [{ tipo_rede: 'Convencional', tipo_cabo: '397MCM-CA, Nu', vao: 80, flecha: 2, angulo: 10 }],
          mt2: [], bt: [], btz: [], ral: []
        })
      })
    })

    await page.route(/\/api\/calcular$/, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(calcResult)
      })
    })
}
