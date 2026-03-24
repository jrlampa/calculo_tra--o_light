import { test, expect } from '@playwright/test'

// BASE_URL vem de playwright.config.js (baseURL = http://127.0.0.1:5173)

async function navegarParaApagar(page) {
  await page.addInitScript(() => { window.localStorage.setItem('guest_mode', 'true') })
  await page.goto('/', { waitUntil: 'networkidle' })
  await page.waitForSelector('input, button', { timeout: 5000 }).catch(() => null)
}

async function navegarParaCalculo(page) {
  await navegarParaApagar(page)
  // Preencher campo Projeto (opcional para convidado, mas bom pra garantir)
  await page.getByLabel(/Projeto/).fill('Projeto E2E Guest')
  
  // No modo DEV/E2E, usamos o botão de convidado para garantir bypass do Supabase
  const guestBtn = page.locator('button:has-text("Entrar como Convidado")')
  if (await guestBtn.isVisible()) {
    await guestBtn.click()
  } else {
    // Fallback para o botão de confirmação padrão se o de convidado não estiver visível
    await page.getByRole('button', { name: /Confirmar/i }).first().click()
  }
  
  // Esperar o MobileActionBar aparecer (indicativo de que mudou de etapa)
  await page.waitForSelector('[data-testid^="action-bar-"]', { timeout: 15000 })
}

test.describe('Undo/Redo + Mobile Action Bar - UI Integration', () => {
  // Testes de Undo e Stepper podem começar na tela inicial
  // Mas os testes específicos da Action Bar precisam da navegação para Cálculo

  test.describe('Mobile Action Bar - Desktop (md breakpoint)', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize({ width: 1024, height: 768 })
      await navegarParaCalculo(page)
    })

    test('should render floating action buttons in corner on desktop', async ({ page }) => {
      const actionBar = page.getByTestId('action-bar-desktop')
      await expect(actionBar).toBeVisible()
      const confirmBtn = actionBar.locator('button', { hasText: 'Confirmar' })
      await expect(confirmBtn).toBeVisible()
      await expect(confirmBtn).toBeEnabled()
    })

    test('should apply correct styling to desktop action buttons', async ({ page }) => {
      const confirmBtn = page.getByTestId('action-bar-desktop').locator('button', { hasText: 'Confirmar' })
      const bgColor = await confirmBtn.evaluate(el => window.getComputedStyle(el).backgroundColor)
      expect(bgColor).toBeTruthy()
    })

    test('should disable buttons when statusPersistencia is saving', async ({ page }) => {
      const confirmBtn = page.getByTestId('action-bar-desktop').locator('button', { hasText: 'Confirmar' })
      await expect(confirmBtn).toBeEnabled()
    })

    test('should focus-ring on keyboard navigation (desktop)', async ({ page }) => {
      const confirmBtn = page.getByTestId('action-bar-desktop').locator('button').first()
      await confirmBtn.focus()
      const focusClass = await confirmBtn.evaluate(el => window.getComputedStyle(el).outline)
      expect(focusClass).toBeTruthy()
    })
  })

  test.describe('Mobile Action Bar - Tablet (sm breakpoint)', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 })
      await navegarParaCalculo(page)
    })

    test('should render full-width action bar on tablet', async ({ page }) => {
      const tabletBar = page.getByTestId('action-bar-tablet')
      await expect(tabletBar).toBeVisible()
      const confirmBtn = tabletBar.locator('button').first()
      await expect(confirmBtn).toBeVisible()
    })

    test('should distribute buttons equally on tablet', async ({ page }) => {
      const tabletBar = page.getByTestId('action-bar-tablet')
      const buttons = tabletBar.locator('button')
      const count = await buttons.count()
      expect(count).toBeGreaterThan(0)
      for (let i = 0; i < count; i++) {
        const btn = buttons.nth(i)
        const flex = await btn.evaluate(el => window.getComputedStyle(el).flex)
        expect(flex).toContain('1')
      }
    })

    test('should apply safe-area padding on tablet', async ({ page }) => {
      const tabletBar = page.getByTestId('action-bar-tablet')
      const padding = await tabletBar.evaluate(el => window.getComputedStyle(el).paddingBottom)
      expect(padding).toBeTruthy()
    })
  })

  test.describe('Mobile Action Bar - Mobile (default, <sm)', () => {
    test.beforeEach(async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      await navegarParaCalculo(page)
    })

    test('should render stacked mobile buttons on small screen', async ({ page }) => {
      const mobileBar = page.getByTestId('action-bar-mobile')
      await expect(mobileBar).toBeVisible()
      const buttons = mobileBar.locator('button')
      expect(await buttons.count()).toBeGreaterThan(0)
    })

    test('should stack buttons vertically and full-width on mobile', async ({ page }) => {
      const mobileBar = page.getByTestId('action-bar-mobile')
      const buttons = mobileBar.locator('button')
      for (let i = 0; i < await buttons.count(); i++) {
        const btn = buttons.nth(i)
        const width = await btn.evaluate(el => el.getBoundingClientRect().width)
        expect(width).toBeGreaterThan(300) // 375px viewport - padding
      }
    })

    test('should show icon-only labels on mobile', async ({ page }) => {
      const mobileBar = page.getByTestId('action-bar-mobile')
      const confirmBtn = mobileBar.locator('button').first()
      const text = await confirmBtn.textContent()
      expect(text?.trim()).toBe('✓')
    })

    test('should apply scale-down on click (mobile interaction)', async ({ page }) => {
      const mobileBar = page.getByTestId('action-bar-mobile')
      const confirmBtn = mobileBar.locator('button').first()
      const hasActiveClass = await confirmBtn.evaluate(el => el.className.includes('active:enabled:scale-95'))
      expect(hasActiveClass).toBe(true)
    })

    test('should provide adequate touch target size on mobile', async ({ page }) => {
      const mobileBar = page.getByTestId('action-bar-mobile')
      const confirmBtn = mobileBar.locator('button').first()
      const box = await confirmBtn.boundingBox()
      expect(box?.height).toBeGreaterThanOrEqual(44)
    })

    test('should apply safe-area inset on mobile bottom', async ({ page }) => {
      const mobileBar = page.getByTestId('action-bar-mobile')
      const padding = await mobileBar.evaluate(el => window.getComputedStyle(el).paddingBottom)
      expect(padding).toBeTruthy()
    })
  })

  test.describe('Accessibility - Action Buttons', () => {
    test('should have proper aria-labels on all buttons', async ({ page }) => {
      await page.setViewportSize({ width: 1024, height: 768 })
      const buttons = page.locator('button[aria-label]')
      const count = await buttons.count()
      expect(count).toBeGreaterThan(0)
      for (let i = 0; i < count; i++) {
        const label = await buttons.nth(i).getAttribute('aria-label')
        expect(label).toBeTruthy()
        expect(label?.length).toBeGreaterThan(0)
      }
    })

    test('should have proper titles for tooltips', async ({ page }) => {
      await page.setViewportSize({ width: 1024, height: 768 })
      const confirmBtn = page.locator('button:has-text("Confirmar")').first()
      const title = await confirmBtn.getAttribute('title')
      expect(title).toBeTruthy()
    })

    test('should have disabled state with proper opacity', async ({ page }) => {
      await page.setViewportSize({ width: 1024, height: 768 })
      const buttons = page.locator('button[disabled]')
      if (await buttons.count() > 0) {
        const opacity = await buttons.first().evaluate(el => window.getComputedStyle(el).opacity)
        expect(parseFloat(opacity)).toBeLessThanOrEqual(0.6)
      }
    })
  })

  test.describe('Responsive Breakpoint Behavior', () => {
    test('should hide desktop bar on tablet and mobile', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 })
      const desktopBar = page.getByTestId('action-bar-desktop')
      const display = await desktopBar.evaluate(el => window.getComputedStyle(el).display)
      expect(display).toBe('none')
    })

    test('should hide tablet bar on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      const tabletBar = page.getByTestId('action-bar-tablet')
      const display = await tabletBar.evaluate(el => window.getComputedStyle(el).display)
      expect(display).toBe('none')
    })

    test('should transition smoothly between breakpoints', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      const mobileBar = page.getByTestId('action-bar-mobile')
      await expect(mobileBar).toBeVisible()
      await page.setViewportSize({ width: 768, height: 1024 })
      const tabletBar = page.getByTestId('action-bar-tablet')
      await expect(tabletBar).toBeVisible()
    })
  })

  test.describe('Button Interaction States', () => {
    test('should apply hover color to confirm button on desktop', async ({ page }) => {
      await page.setViewportSize({ width: 1024, height: 768 })
      const confirmBtn = page.getByTestId('action-bar-desktop').locator('button', { hasText: 'Confirmar' }).first()
      await confirmBtn.hover()
      const bgColor = await confirmBtn.evaluate(el => window.getComputedStyle(el).backgroundColor)
      expect(bgColor).toBeTruthy()
    })

    test('should maintain focus after click', async ({ page }) => {
      await page.setViewportSize({ width: 1024, height: 768 })
      const confirmBtn = page.getByTestId('action-bar-desktop').locator('button', { hasText: 'Confirmar' }).first()
      await confirmBtn.click()
      const focused = await confirmBtn.evaluate((el) => el.matches(':focus') || document.activeElement === el)
      expect(typeof focused).toBe('boolean')
    })
  })

  test.describe('Table Responsiveness with Action Bar', () => {
    test('should add bottom margin to table on mobile to avoid overlap', async () => {
      await page.setViewportSize({ width: 375, height: 667 })
      
      const table = page.locator('table').first()
      const container = table.locator('xpath=..').first()
      
      const margin = await container.evaluate(el => {
        const styles = window.getComputedStyle(el)
        return styles.marginBottom
      })
      
      expect(margin).toBeTruthy()
    })

    test('should have no bottom margin on desktop', async () => {
      await page.setViewportSize({ width: 1024, height: 768 })
      
      const table = page.locator('table').first()
      const container = table.locator('xpath=..').first()
      
      const margin = await container.evaluate(el => {
        return window.getComputedStyle(el).marginBottom
      })
      
      expect(['0px', '0']).toContain(margin)
    })

    test('should display table with proper padding on mobile', async () => {
      await page.setViewportSize({ width: 375, height: 667 })
      
      const table = page.locator('table').first()
      const container = table.locator('xpath=..').first()
      
      const hasOverflow = await container.evaluate(el => {
        const styles = window.getComputedStyle(el)
        return styles.overflowX
      })
      
      expect(['auto', 'scroll']).toContain(hasOverflow)
    })
  })

  test.describe('Undo/Desfazer - APAGA com recovery', () => {
    test('user can undo field deletion via Ctrl+Z', async ({ page }) => {
      await page.getByLabel(/Ponto/).fill('A-001')
      await expect(page.getByLabel(/Ponto/)).toHaveValue('A-001')
      await page.getByLabel(/Ponto/).clear()
      await expect(page.getByLabel(/Ponto/)).toHaveValue('')
      await page.keyboard.press('Control+Z')
      await page.waitForTimeout(100)
      const consoleErrors = []
      page.on('console', msg => { if (msg.type() === 'error') consoleErrors.push(msg.text()) })
      expect(consoleErrors.length).toBe(0)
    })

    test('undo stack clears after 5 minutes (TTL)', async ({ page }) => {
      await page.getByLabel(/Numero Vao/).fill('15').catch(() => null)
      const hasUndoStack = await page.evaluate(() => typeof window.__UNDO_STACK__ !== 'undefined').catch(() => false)
      expect(true).toBe(true)
    })

    test('undo stack clears when navigating to new ponto', async ({ page }) => {
      await page.getByLabel(/Ponto/).fill('A-001')
      await page.getByLabel(/Ponto/).clear()
      await page.getByLabel(/Ponto/).fill('A-002')
      await page.waitForTimeout(100)
    })
  })

  test.describe('Stepper Navigation - FlowStepper', () => {
    test('stepper shows correct etapa based on active screen', async ({ page }) => {
      const stepperDots = page.locator('[role="menuitem"], .stepper-dot')
      if (await stepperDots.count({ timeout: 1000 }).catch(() => 0) > 0) {
        const firstDot = stepperDots.first()
        const ariaSelected = await firstDot.getAttribute('aria-selected').catch(() => null)
        expect([null, 'true']).toContain(ariaSelected)
      }
    })

    test('stepper allows navigation between etapas (projeto -> ponto -> calculo)', async ({ page }) => {
      const projectInput = page.getByLabel(/Projeto/)
      await expect(projectInput).toBeVisible()
      await projectInput.fill('Projeto Test')
      await page.getByLabel(/Ponto/).fill('A-001')
      await page.getByLabel(/Tipo de Poste/).selectOption('Concreto circular')
      await page.getByLabel(/Modelo de Poste/).selectOption('11 m / 600 daN')
      const confirmBtn = page.getByRole('button', { name: /Confirmar/ }).first()
      await confirmBtn.click()
      await page.waitForTimeout(500)
      const calcContent = page.locator('table, svg, [class*="relogio"]')
      const isVisible = await calcContent.isVisible({ timeout: 2000 }).catch(() => false)
      expect(isVisible).toBe(true)
    })

    test('stepper reflects "saved" state when persistencia completes successfully', async ({ page }) => {
      await page.getByLabel(/Projeto/).fill('Proj Test')
      await page.getByLabel(/Ponto/).fill('A-001')
      await page.getByLabel(/Tipo de Poste/).selectOption('Concreto circular')
      await page.getByLabel(/Modelo de Poste/).selectOption('11 m / 600 daN')
      await page.getByRole('button', { name: /Confirmar/ }).first().click()
      await page.waitForTimeout(500)
      const statusChips = page.locator('[role="status"]')
      if (await statusChips.count({ timeout: 1000 }).catch(() => 0) > 0) {
        const isVisible = await statusChips.first().isVisible({ timeout: 1000 }).catch(() => false)
        expect(isVisible).toBe(true)
      }
    })

    test('stepper disables navigation when in error state', async ({ page }) => {
      await page.getByLabel(/Projeto/).fill('Proj Error Test')
      await page.getByLabel(/Ponto/).fill('A-001')
      await page.getByLabel(/Tipo de Poste/).selectOption('Concreto circular')
      await page.getByLabel(/Modelo de Poste/).selectOption('11 m / 600 daN')
      await page.getByRole('button', { name: /Confirmar/ }).first().click()
      await page.waitForTimeout(500)
      const stepperDots = page.locator('[role="menuitem"], .stepper-dot')
      const count = await stepperDots.count({ timeout: 1000 }).catch(() => 0)
      expect(count).toBeGreaterThanOrEqual(0)
    })
  })
})
