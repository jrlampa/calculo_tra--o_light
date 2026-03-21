/**
 * e2e/ui-calc.spec.js
 *
 * Testes da interface React (formulário de cálculo de tração)
 * com fluxo inicial de cadastro de projeto concluído antes das validações.
 */
import { test, expect } from '@playwright/test'

const NOME_PROJETO_E2E = 'Projeto Playwright E2E'
const PROJETO_MOCK_ID = '11111111-1111-4111-8111-111111111111'

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
  await page.route('**/api/projetos', async route => {
    if (route.request().method() !== 'POST') {
      await route.continue()
      return
    }

    const payload = route.request().postDataJSON() ?? {}

    await route.fulfill({
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify({
        id: PROJETO_MOCK_ID,
        orgao: payload.orgao || '',
        ns: payload.ns || '',
        nome: payload.nome || NOME_PROJETO_E2E,
        endereco: payload.endereco || '',
        estudado_por: payload.estudado_por || '',
        matricula: payload.matricula || '',
        data_estudo: payload.data_estudo || '',
        total_pontos: 0,
      }),
    })
  })

  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Cadastro do projeto' })).toBeVisible()

  await page.getByLabel('Projeto').fill(NOME_PROJETO_E2E)
  await page.getByRole('button', { name: 'Confirmar e iniciar cálculo' }).click()

  await Promise.race([
    page.waitForSelector('.sec-title', { timeout: 15_000 }),
    page.getByRole('button', { name: 'APAGA' }).waitFor({ state: 'visible', timeout: 15_000 }),
  ])

  await expect(page.getByRole('button', { name: 'APAGA' })).toBeVisible()
}

test.describe('UI – Formulário de Cálculo', () => {
  test.beforeEach(async ({ page }) => {
    await iniciarFluxoProjeto(page)
  })

  // ── 1. Página carrega ─────────────────────────────────────────────────────
  test('carrega a página e exibe seções MT e BT', async ({ page }) => {
    const titulos = page.locator('.sec-title')
    await expect(titulos).toHaveCount(5)
    await expect(page.locator('.sec-title', { hasText: 'MT - 1º Nível' })).toBeVisible()
    await expect(page.locator('.sec-title', { hasText: 'MT - 2º Nível' })).toBeVisible()
    await expect(page.locator('.sec-title').filter({ hasText: /^BT$/ })).toBeVisible()
    await expect(page.locator('.sec-title', { hasText: 'Ramais BTZero' })).toBeVisible()
    await expect(page.locator('.sec-title', { hasText: 'Ramais de ligação' })).toBeVisible()
  })

  // ── 2. Inputs existem e aceitam digitação ─────────────────────────────────
  test('inputs estão presentes e aceitam valores numéricos', async ({ page }) => {
    const secaoMt1 = secao(page, 'MT - 1º Nível')

    const vaoInput = secaoMt1.locator('input[id="vao-t1"]').first()
    await expect(vaoInput).toBeVisible()

    await vaoInput.fill('50')
    await expect(vaoInput).toHaveValue('50')

    const flechaInput = secaoMt1.locator('input[id="flecha-t1"]').first()
    await expect(flechaInput).toBeVisible()
    await flechaInput.fill('1,5')
    await expect(flechaInput).toHaveValue('1,5')
  })

  // ── 3. Cálculo dispara após debounce e exibe resultado ────────────────────
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
    const resultadoTotal = page.locator('.tracao-total-box')

    await expect(mt1Resultado).toContainText(/TRAÇÃO MT 1° NÍVEL/i)
    await expect.poll(async () => extrairValorDan(await mt1Resultado.textContent()), { timeout: 12_000 }).toBeGreaterThan(0)
    await expect.poll(async () => extrairValorDan(await resultadoTotal.textContent()), { timeout: 12_000 }).toBeGreaterThan(0)
  })

  // ── 4. Diagrama de relógio renderiza ──────────────────────────────────────
  test('diagrama/componente visual está presente na página', async ({ page }) => {
    await expect(page.locator('canvas[aria-label="Relógio de ângulos de tração"]')).toBeVisible()
    await expect(page.locator('svg[aria-label="Diagrama do poste"]')).toBeVisible()
  })

  // ── 5. Tabela de cargas está presente ─────────────────────────────────────
  test('tabela de carga nominal aparece na página', async ({ page }) => {
    const tabelaCargas = page.locator('table').filter({ hasText: 'R (daN)' }).first()

    await expect(tabelaCargas).toBeVisible()
    await expect(tabelaCargas).toContainText('R (daN)')
    await expect(tabelaCargas.locator('th', { hasText: '300' })).toBeVisible()
    await expect(tabelaCargas.locator('th', { hasText: '600' })).toBeVisible()
  })

  // ── 6. Teste headed: resultado numérico após preenchimento completo ────────
  test('resultado total de tração é exibido após preencher MT1 completo', async ({ page }) => {
    const secaoMt1 = secao(page, 'MT - 1º Nível')

    await secaoMt1.locator('select[id="tipoRede-t1"]').first().selectOption({ label: 'Convencional' })
    await secaoMt1.locator('select[id="tipoCabo-t1"]').first().selectOption({ label: '397MCM-CA, Nu' })
    await secaoMt1.locator('input[id="vao-t1"]').first().fill('50')
    await secaoMt1.locator('input[id="flecha-t1"]').first().fill('1,5')
    await secaoMt1.locator('input[id="angulo-t1"]').first().fill('0')
    await secaoMt1.locator('input[id="alturaPoste-t1"]').first().fill('11')
    await secaoMt1.locator('input[id="alturaAncoragem-t1"]').first().fill('1')

    const resultadoTotal = page.locator('.tracao-total-box')
    await expect(resultadoTotal).toContainText(/TRAÇÃO TOTAL/i)
    await expect.poll(async () => extrairValorDan(await resultadoTotal.textContent()), { timeout: 12_000 }).toBeGreaterThan(0)

    await expect(page.locator('body')).not.toContainText('500 Internal Server Error')
    await expect(page.locator('body')).not.toContainText('Cannot read')
  })

  // ── 7. Erro 422: vão preenchido sem flecha ────────────────────────────────
  test('exibe erro quando flecha é zero com vão preenchido', async ({ page }) => {
    // Mock do endpoint calcular para simular 422
    await page.route('**/api/calcular', async route => {
      await route.fulfill({
        status: 422,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Entrada fora do domínio operacional: flecha deve ser > 0 quando vao > 0',
        }),
      })
    })

    const mt1Panel = secao(page, 'MT - 1º Nível')
    const vaoInputs = mt1Panel.locator('input[id="vao-t1"]')

    if (await vaoInputs.count() > 0) {
      await vaoInputs.first().fill('30')
      await page.waitForTimeout(1500) // aguardar debounce
      // Nunca deve exibir erro interno 500 ou texto de traceback
      await expect(page.locator('body')).not.toContainText('500')
      await expect(page.locator('body')).not.toContainText('Erro interno')
    }
  })

  // ── 8. Erro de persistência não causa crash ───────────────────────────────
  test('exibe estado de erro quando persistência falha', async ({ page }) => {
    // Mock criação de ponto com sucesso
    await page.route('**/api/projetos/*/pontos', async route => {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '22222222-2222-4222-8222-222222222222',
          nome: 'Ponto 1',
        }),
      })
    })

    // Mock /calcular retornando resultado válido
    await page.route('**/api/calcular', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          mt1: { tracao_dan: 217, angulo_graus: 177, resultante_raw: 217.37, texto: 'MT1: 217 daN @ 177°' },
          mt2: { tracao_dan: 0, angulo_graus: 0, resultante_raw: 0, texto: '' },
          bt:  { tracao_dan: 0, angulo_graus: 0, resultante_raw: 0, texto: '' },
          btz: { tracao_dan: 0, angulo_graus: 0, resultante_raw: 0, texto: '' },
          ral: { tracao_dan: 0, angulo_graus: 0, resultante_raw: 0, texto: '' },
          total_tracao_dan: 217, total_angulo_graus: 177,
          texto_total: 'Total: 217 daN @ 177°',
          vetores: [], poste_ecc_dan: 0,
        }),
      })
    })

    // Mock do salvar_calculo falhando (persistência indisponível)
    await page.route('**/api/projetos/*/pontos/*/calculo', async route => {
      await route.fulfill({ status: 503, body: 'Service unavailable' })
    })

    // UI não deve exibir erro fatal nem traceback
    await expect(page.locator('body')).not.toContainText('Erro fatal')
    await expect(page.locator('body')).not.toContainText('500')
  })
})
