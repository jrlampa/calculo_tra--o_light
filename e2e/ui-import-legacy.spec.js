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
    const guestBtn = page.getByRole('button', { name: /Entrar como Convidado/i })
    await guestBtn.click()
    
    await page.waitForSelector('.calc-side-column', { timeout: 15000 })
  })

  test('deve importar dados do Excel e disparar cálculo com sobrecarga', async ({ page }) => {
    // 1. Mock do endpoint de Importação
    await page.route('**/api/calcular/importar-excel', async route => {
      console.log('E2E MOCK: Intercepted IMPORT call')
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          cabecalho: { projeto: 'LEGADO PROJ', ponto: 'P1' },
          poste: { tipo_poste: 'Concreto Duplo T', modelo_poste: 'DT 11/600' },
          mt1: [
              { tipo_rede: 'Convencional', tipo_cabo: '397MCM-CA, Nu', vao: 80, flecha: 2, angulo: 10, altura_poste: 11, altura_ancoragem: 1 },
              { tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, altura_poste: 0, altura_ancoragem: 0 },
              { tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, altura_poste: 0, altura_ancoragem: 0 },
              { tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, altura_poste: 0, altura_ancoragem: 0 }
          ],
          mt2: [], bt: [], btz: [], ral: []
        })
      })
    })

    // 2. Mock do endpoint de Cálculo (Regex para garantir interceptação)
    await page.route(/\/api\/calcular$/, async route => {
      console.log(`E2E MOCK: Intercepted CALC call to ${route.request().url()}`)
      const payload = route.request().postDataJSON()
      console.log('E2E MOCK: Calc Payload VAO-T1 =', payload?.mt1?.[0]?.vao)
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total_tracao_dan: 999,
          total_angulo_graus: 10.2,
          texto_total: "TRAÇÃO TOTAL: 999 daN 10° [SOBRECARGA]",
          status_poste: "SOBRECARGA",
          resistencia_nominal: 600,
          vetores: []
        })
      })
    })

    // 3. Acionar Importação (Mockado via clique no botão que dispara o input)
    // Como não podemos simular o seletor de arquivos nativo facilmente em mock puro sem interagir com o input oculto,
    // vamos disparar o evento de mudança no input manualmente ou usar setInputFiles.
    
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles({
      name: 'projeto-legado.xlsm',
      mimeType: 'application/vnd.ms-excel.sheet.macroEnabled.12',
      buffer: Buffer.from('')
    })

    // Aguardar estabilização do cálculo (Debounce + Fetch)
    await page.waitForTimeout(2000)

    // 4. Verificar se os campos foram preenchidos
    await expect(page.locator('input[id="vao-t1"]').first()).toHaveValue('80')
    
    // 5. Verificar o resultado de Tração com aviso de sobrecarga
    const tracaoTotalBox = page.locator('.tracao-total-box')
    await expect(tracaoTotalBox).toContainText(/999 daN/i, { timeout: 15000 })
    await expect(tracaoTotalBox).toContainText(/\[SOBRECARGA\]/i, { timeout: 15000 })
    console.log('E2E SUCCESS: Sobrecarga detected in UI')
  })
})
