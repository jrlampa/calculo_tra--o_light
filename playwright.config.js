import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright config – testes locais (Chromium apenas).
 *
 * Pré-requisito: ter os servidores rodando, OU deixar o playright
 * iniciá-los automaticamente via webServer.
 *
 * Modo manual (recomendado durante desenvolvimento):
 *   Terminal 1:  npm run dev:full
 *   Terminal 2:  npm run test:e2e
 *
 * Modo automático (playwright sobe os servidores):
 *   npm run test:e2e          (sem servidores rodando)
 */
export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  expect: { timeout: 10_000 },

  // Rodar testes em série dentro de cada arquivo
  fullyParallel: false,
  retries: 0,
  workers: 1,

  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
  ],

  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  webServer: [
    // ── Vite (React UI) ──────────────────────────────────────────────────
    {
      command: 'npm run dev',
      url: 'http://localhost:5173',
      reuseExistingServer: true,
      timeout: 30_000,
      stdout: 'ignore',
      stderr: 'pipe',
    },
    // ── FastAPI (Python backend) ─────────────────────────────────────────
    {
      command: 'npm run test:serve:api',
        url: 'http://localhost:8001/health',
      reuseExistingServer: true,
      timeout: 30_000,
      stdout: 'ignore',
      stderr: 'pipe',
    },
  ],
})
