/**
 * e2e/ui-calc.spec.js
 */
import { test, expect } from '@playwright/test'

const NOME_PROJETO_E2E = 'Projeto Playwright E2E'
const PROJETO_MOCK_ID = '11111111-1111-4111-8111-111111111111'

// Aumentar timeout para este arquivo de debug
test.setTimeout(60000);

function secao(page, titulo) {
  return page
    .locator('.sec-panel')
    .filter({ has: page.locator('.sec-title', { hasText: titulo }) })
    .first()
}

function extrairValorDan(texto) {
  const match = (texto || '').match(/:\s*(-?\d+(?:[.,]\d+)?)\s*daN/i)
  if (!match) return 0
  const valor = Number(match[1].replace(',', '.'))
  return Number.isNaN(valor) ? 0 : valor
}

async function iniciarFluxoProjeto(page) {
  console.log('--- START iniciarFluxoProjeto ---');
  
  // Mock API
  await page.route(url => url.pathname.includes('/api/projetos'), async route => {
    console.log(`MOCK: Intercepted ${route.request().method()} to ${route.request().url()}`);
    const payload = route.request().postDataJSON() ?? {}
    await route.fulfill({
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify({
        id: PROJETO_MOCK_ID,
        nome: payload.nome || NOME_PROJETO_E2E,
        total_pontos: 0,
      }),
    })
    console.log('MOCK: 201 Response Sent');
  })

  await page.addInitScript(() => {
    window.localStorage.setItem('guest_mode', 'true');
    console.log('localStorage.guest_mode set');
  });

  console.log('Navigating...');
  await page.goto('/', { waitUntil: 'networkidle' })
  
  console.log('Waiting for heading...');
  const heading = page.getByRole('heading', { name: /Cadastro do projeto/i });
  await expect(heading).toBeVisible({ timeout: 15000 });

  console.log('Filling PROJECT field...');
  await page.getByLabel('Projeto').fill(NOME_PROJETO_E2E)
  
  console.log('Clicking CONFIRMAR...');
  const submitBtn = page.getByRole('button', { name: /Confirmar/i });
  await expect(submitBtn).toBeEnabled();
  await submitBtn.click();

  console.log('Waiting for transition...');
  await page.waitForSelector('.sec-title', { timeout: 20000 }).catch(async (e) => {
    console.log('TIMEOUT TRANSITION. Screenshot saved.');
    await page.screenshot({ path: 'e2e-hang.png' });
    throw e;
  });

  console.log('Checking APAGA button...');
  await expect(page.getByRole('button', { name: 'APAGA' })).toBeVisible()
  console.log('--- END iniciarFluxoProjeto ---');
}

test.describe('UI – Formulário de Cálculo', () => {
  test.beforeEach(async ({ page }) => {
    await iniciarFluxoProjeto(page)
  })

  test('carrega a página e exibe seções MT e BT', async ({ page }) => {
    const titulos = page.locator('.sec-title')
    await expect(titulos).toHaveCount(5)
    await expect(page.locator('.sec-title', { hasText: 'MT - 1º Nível' })).toBeVisible()
  })

  test('preencher MT1 dispara cálculo e res-lbl atualiza', async ({ page }) => {
    const secaoMt1 = secao(page, 'MT - 1º Nível')
    await secaoMt1.locator('select[id="tipoRede-t1"]').first().selectOption({ label: 'Convencional' })
    await secaoMt1.locator('select[id="tipoCabo-t1"]').first().selectOption({ label: '397MCM-CA, Nu' })
    await secaoMt1.locator('input[id="vao-t1"]').first().fill('50')
    await secaoMt1.locator('input[id="flecha-t1"]').first().fill('1,5')
    await secaoMt1.locator('input[id="angulo-t1"]').first().fill('0')
    await secaoMt1.locator('input[id="alturaPoste-t1"]').first().fill('11')
    await secaoMt1.locator('input[id="alturaAncoragem-t1"]').first().fill('1')

    const mt1Resultado = secaoMt1.locator('.res-lbl')
    await expect(mt1Resultado).toContainText(/TRAÇÃO MT 1° NÍVEL/i)
    await expect.poll(async () => extrairValorDan(await mt1Resultado.textContent()), { timeout: 15_000 }).toBeGreaterThan(0)
  })
})
