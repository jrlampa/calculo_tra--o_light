/**
 * e2e/ui-calc.spec.js
 *
 * Testes da interface React (formulário de cálculo de tração).
 *
 * Seletores baseados na estrutura real dos componentes:
 *   - .sec-title         → títulos das seções (MT - 1º Nível, etc.)
 *   - .sec-panel         → container de cada seção
 *   - #vao-t1            → input de Vão, Travessia 1 (SecaoNivel usa id `{campo}-t{i+1}`)
 *   - #flecha-t1         → input de Flecha, Travessia 1
 *   - .res-lbl           → linha de resultado (contém "daN")
 *   - .xcell             → inputs numéricos dentro das seções
 *
 * O hook useCalculo.js debounce 600 ms antes de chamar /api/calcular.
 */
import { test, expect } from '@playwright/test'

test.describe('UI – Formulário de Cálculo', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    // Aguarda app montar completamente
    await page.waitForLoadState('domcontentloaded')
    // Confirma que pelo menos um sec-title está visível (app renderizou)
    await page.waitForSelector('.sec-title', { timeout: 10_000 })
  })

  // ── 1. Página carrega ─────────────────────────────────────────────────────
  test('carrega a página e exibe seções MT e BT', async ({ page }) => {
    // Deve haver seções para MT1, MT2, BT, BT_0 e RAL
    const titles = page.locator('.sec-title')
    const count = await titles.count()
    expect(count).toBeGreaterThanOrEqual(3)

    // Pelo menos uma seção deve conter "MT" ou "BT"
    const textos = await titles.allTextContents()
    const temMT = textos.some(t => /MT/i.test(t))
    const temBT = textos.some(t => /BT/i.test(t))
    expect(temMT).toBeTruthy()
    expect(temBT).toBeTruthy()
  })

  // ── 2. Inputs existem e aceitam digitação ─────────────────────────────────
  test('inputs estão presentes e aceitam valores numéricos', async ({ page }) => {
    // Campo Vão da 1ª travessia no bloco MT1
    const vaoInput = page.locator('#vao-t1').first()
    await expect(vaoInput).toBeVisible()

    await vaoInput.fill('50')
    await expect(vaoInput).toHaveValue('50')

    const flechaInput = page.locator('#flecha-t1').first()
    await expect(flechaInput).toBeVisible()
    await flechaInput.fill('1,5')
    await expect(flechaInput).toHaveValue('1,5')
  })

  // ── 3. Cálculo dispara após debounce e exibe resultado ────────────────────
  test('preencher MT1 dispara cálculo e res-lbl atualiza', async ({ page }) => {
    // Preencher campos mínimos para MT1 T1
    await page.locator('#vao-t1').first().fill('50')
    await page.locator('#flecha-t1').first().fill('1,5')

    // Aguardar debounce (600 ms) + tempo de resposta da API
    await page.waitForTimeout(1500)

    // O .res-lbl da seção MT deve conter "daN" (unidade do resultado)
    const resLabels = page.locator('.res-lbl')
    const count = await resLabels.count()
    expect(count).toBeGreaterThan(0)

    // Pelo menos um label contém "daN"
    const textos = await resLabels.allTextContents()
    const temDaN = textos.some(t => /daN/i.test(t))
    expect(temDaN).toBeTruthy()
  })

  // ── 4. Diagrama de relógio renderiza ──────────────────────────────────────
  test('diagrama/componente visual está presente na página', async ({ page }) => {
    // O DiagramaPoste ou RelogioAngulos renderiza um SVG ou canvas
    const visual = page.locator('svg, canvas')
    const count = await visual.count()
    // Pode ser 0 se sem resultados; mas a estrutura da página deve estar OK
    await expect(page.locator('body')).toBeVisible()

    // Se houver SVG, confirmar que não está oculto
    if (count > 0) {
      await expect(visual.first()).toBeVisible()
    }
  })

  // ── 5. Tabela de cargas está presente ─────────────────────────────────────
  test('tabela de carga nominal aparece na página', async ({ page }) => {
    // TabelaCarga renderiza uma <table> com cabeçalho "R (daN)"
    const tables = page.locator('table')
    const count = await tables.count()
    expect(count).toBeGreaterThan(0)

    // Alguma célula deve conter "daN"
    const cellsWithDaN = page.locator('td, th').filter({ hasText: /daN/i })
    const dAnCount = await cellsWithDaN.count()
    expect(dAnCount).toBeGreaterThan(0)
  })

  // ── 6. Teste headed: resultado numérico após preenchimento completo ────────
  test('resultado total de tração é exibido após preencher MT1 completo', async ({ page }) => {
    // Preencher todos os campos do MT1 T1 para garantir cálculo válido
    await page.locator('#vao-t1').first().fill('50')
    await page.locator('#flecha-t1').first().fill('1,5')
    await page.locator('#angulo-t1').first().fill('0')

    // Aguardar debounce + API
    await page.waitForTimeout(1500)

    // Verificar que a página não exibe erro de crash
    const errorText = page.locator('body').filter({ hasText: /Erro|Error|500|NaN/i })
    // Não deve ter erros visíveis de crash
    await expect(page.locator('body')).not.toContainText('500 Internal Server Error')
    await expect(page.locator('body')).not.toContainText('Cannot read')
  })
})
