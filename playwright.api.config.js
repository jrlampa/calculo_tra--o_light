/**
 * Playwright config — API Smoke Tests only.
 *
 * Usar quando o servidor FastAPI já está rodando:
 *   npx playwright test --config=playwright.api.config.js --reporter=list
 *
 * Sem webServer: evita conflitos de IPv4/IPv6 no Windows.
 */
import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  testMatch: ['**/api-health.spec.js'],
  timeout: 30_000,
  expect: { timeout: 10_000 },

  fullyParallel: false,
  retries: 0,
  workers: 1,

  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
  ],

  use: {
    // Sem baseURL pois são testes de API pura (request fixture)
    trace: 'on-first-retry',
  },

  // Sem webServer — requer que o servidor já esteja rodando:
  //   python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
})
