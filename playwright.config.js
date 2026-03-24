import { defineConfig, devices } from '@playwright/test'

const E2E_UI_PORT = 5173
const E2E_UI_URL = process.env.E2E_UI_URL || 'http://127.0.0.1:5173'
const E2E_API_PORT = 8000
const E2E_API_URL = process.env.E2E_API_URL || `http://127.0.0.1:${E2E_API_PORT}`
const DEFAULT_E2E_API_COMMAND = process.platform === 'win32'
  ? `cd python && (..\\.venv\\Scripts\\python.exe -m uvicorn api.main:app --port ${E2E_API_PORT} || python -m uvicorn api.main:app --port ${E2E_API_PORT})`
  : `cd python && python -m uvicorn api.main:app --port ${E2E_API_PORT}`
const E2E_API_COMMAND = process.env.E2E_API_COMMAND || DEFAULT_E2E_API_COMMAND

process.env.E2E_API_URL = E2E_API_URL

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
    baseURL: E2E_UI_URL,
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
      command: `npm run dev -- --port ${E2E_UI_PORT}`,
      url: E2E_UI_URL,
      reuseExistingServer: true,
      timeout: 30_000,
      env: {
        ...process.env,
        VITE_API_PROXY_TARGET: E2E_API_URL,
      },
      stdout: 'ignore',
      stderr: 'pipe',
    },
    // ── FastAPI (Python backend) ─────────────────────────────────────────
    {
      command: E2E_API_COMMAND,
      url: `${E2E_API_URL}/health`,
      reuseExistingServer: true,
      timeout: 30_000,
      stdout: 'ignore',
      stderr: 'pipe',
    },
  ],
})
