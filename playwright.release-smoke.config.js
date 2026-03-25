import { defineConfig } from '@playwright/test';

const E2E_API_PORT = 8000;
const E2E_API_URL = process.env.E2E_API_URL || `http://127.0.0.1:${E2E_API_PORT}`;
const RELEASE_SMOKE_JWT_SECRET =
  process.env.AUTH_JWT_SECRET || 'release-smoke-default-secret';
const DEFAULT_E2E_API_COMMAND = process.platform === 'win32'
  ? `cd python && (..\\.venv\\Scripts\\python.exe -m uvicorn api.main:app --port ${E2E_API_PORT} || python -m uvicorn api.main:app --port ${E2E_API_PORT})`
  : `cd python && python -m uvicorn api.main:app --port ${E2E_API_PORT}`;
const E2E_API_COMMAND = process.env.E2E_API_COMMAND || DEFAULT_E2E_API_COMMAND;

process.env.API_URL = process.env.API_URL || `${E2E_API_URL}/api`;
process.env.AUTH_JWT_SECRET = RELEASE_SMOKE_JWT_SECRET;
process.env.AUTH_REQUIRE_JWT_FOR_MUTATIONS =
  process.env.AUTH_REQUIRE_JWT_FOR_MUTATIONS || 'true';
process.env.AUTH_REQUIRE_JWT_FOR_WRITES =
  process.env.AUTH_REQUIRE_JWT_FOR_WRITES || 'true';

export default defineConfig({
  testDir: './e2e',
  testMatch: ['**/release-smoke-critical.spec.js'],
  timeout: 30_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: [['list']],
  use: {
    trace: 'off',
  },
  webServer: {
    command: E2E_API_COMMAND,
    url: `${E2E_API_URL}/health`,
    reuseExistingServer: true,
    timeout: 30_000,
    stdout: 'ignore',
    stderr: 'pipe',
    env: {
      ...process.env,
      E2E_API_URL,
      API_URL: process.env.API_URL || `${E2E_API_URL}/api`,
      AUTH_JWT_SECRET: RELEASE_SMOKE_JWT_SECRET,
      AUTH_REQUIRE_JWT_FOR_MUTATIONS:
        process.env.AUTH_REQUIRE_JWT_FOR_MUTATIONS || 'true',
      AUTH_REQUIRE_JWT_FOR_WRITES:
        process.env.AUTH_REQUIRE_JWT_FOR_WRITES || 'true',
    },
  },
});
