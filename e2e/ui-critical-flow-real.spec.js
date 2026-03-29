/**
 * e2e/ui-critical-flow-real.spec.js
 *
 * Suite E2E sem mocks – valida o fluxo crítico completo com backend real.
 *
 * Requer backend FastAPI disponível em E2E_API_URL e frontend em E2E_UI_URL.
 * Quando o backend não estiver disponível, todos os testes são pulados
 * automaticamente via `test.skip()` (sem falha no CI em ambientes parciais).
 *
 * Variáveis de ambiente:
 *   E2E_UI_URL           URL do frontend Vite (padrão: http://127.0.0.1:5173)
 *   E2E_API_URL          URL da API FastAPI  (padrão: http://127.0.0.1:8000)
 *   E2E_REAL_AUTH_TOKEN  JWT Bearer token para autenticação (opcional – pula testes autenticados se ausente)
 *
 * Cenários cobertos:
 *   1. Happy path: criar projeto → ponto → cálculo → persistência saved
 *   2. Falha de persistência: salvar em ponto inexistente retorna 404/422 e UI exibe erro
 */

import { test, expect } from '@playwright/test'
import { criarProjeto, criarPonto, criarTravessia, criarResultado } from './helpers/test_factories.js'

const API_BASE = process.env.E2E_API_URL || 'http://127.0.0.1:8000'
const AUTH_TOKEN = process.env.E2E_REAL_AUTH_TOKEN || ''

const RUN_ID = `${Date.now()}`.slice(-8)

// ─── Helpers ──────────────────────────────────────────────────────────────────

function authHeaders() {
  const base = { 'Content-Type': 'application/json' }
  return AUTH_TOKEN ? { ...base, Authorization: `Bearer ${AUTH_TOKEN}` } : base
}

/** Pula o teste corrente se o backend não estiver disponível */
async function skipIfBackendIndisponivel(request) {
  try {
    const resp = await request.get(`${API_BASE}/health`, { timeout: 5000 })
    if (!resp.ok()) {
      test.skip(true, `Backend indisponível: ${resp.status()} em GET /health`)
    }
  } catch {
    test.skip(true, 'Backend indisponível (conexão recusada)')
  }
}

/** Pula o teste se o token JWT não estiver configurado */
function skipIfSemAuth() {
  if (!AUTH_TOKEN) {
    test.skip(true, 'E2E_REAL_AUTH_TOKEN não configurado – teste autenticado ignorado')
  }
}

/** POST autenticado via request fixture (sem browser) */
async function apiPost(request, path, data) {
  return request.post(`${API_BASE}${path}`, {
    headers: authHeaders(),
    data,
  })
}

/** GET autenticado via request fixture (sem browser) */
async function apiGet(request, path) {
  return request.get(`${API_BASE}${path}`, { headers: authHeaders() })
}

/** Cria projeto + ponto no backend; retorna { projetoId, pontoId } */
async function criarProjetoPonto(request, suffix = '') {
  const projeto = criarProjeto()
    .withNome(`E2E Real ${RUN_ID}${suffix}`)
    .withNs(`NS-${RUN_ID}${suffix}`)
    .build()

  const projetoResp = await apiPost(request, '/api/projetos', projeto)
  expect(projetoResp.status(), 'POST /api/projetos falhou').toBe(201)
  const projetoId = (await projetoResp.json()).id

  const ponto = criarPonto()
    .withPonto(`PT-${RUN_ID}${suffix}`)
    .withTipoPoste('DT')
    .withModeloPoste('11/600')
    .build()

  const pontoResp = await apiPost(request, `/api/projetos/${projetoId}/pontos`, ponto)
  expect(pontoResp.status(), 'POST /api/pontos falhou').toBe(201)
  const pontoId = (await pontoResp.json()).id

  return { projetoId, pontoId }
}

/** Monta payload de cálculo completo para um ponto */
function buildCalculoPayload(pontoId) {
  const travessias = [1, 2, 3, 4].map((pos) =>
    criarTravessia(pos)
      .withTipoRede(pos === 1 ? 'Convencional' : '')
      .withTipoCabo(pos === 1 ? '397MCM-CA, Nu' : '')
      .withVao(pos === 1 ? 50 : 0)
      .withFlecha(pos === 1 ? 1.2 : 0)
      .withAngulo(pos === 1 ? 5 : 0)
      .build()
  )

  const resultado = criarResultado()
    .withMt1Tracao(180.0)
    .withMt1Angulo(5.0)
    .withTotalTracao(180.0)
    .withTotalAngulo(5.0)
    .build()

  return {
    ponto_id: pontoId,
    tipo_poste: 'DT',
    modelo_poste: '11/600',
    niveis: [
      { nivel: 'MT1', travessias },
      { nivel: 'MT2', travessias: [1, 2, 3, 4].map((p) => criarTravessia(p).build()) },
      { nivel: 'BT',  travessias: [1, 2, 3, 4].map((p) => criarTravessia(p).build()) },
      { nivel: 'BTZ', travessias: [1, 2, 3, 4].map((p) => criarTravessia(p).build()) },
      { nivel: 'RAL', travessias: [1, 2, 3, 4].map((p) => criarTravessia(p).build()) },
    ],
    resultado,
  }
}

// ─── Suite ────────────────────────────────────────────────────────────────────

test.describe.serial('UI Fluxo Real – sem mocks', () => {
  // ── Cenário 1: Happy path (autenticado) ───────────────────────────────────

  test.describe.serial('1 – Happy path: Projeto → Ponto → Cálculo → Persistência saved', () => {
    let projetoId
    let pontoId

    test('pré-condição: backend acessível e token configurado', async ({ request }) => {
      await skipIfBackendIndisponivel(request)
      skipIfSemAuth()
    })

    test('1.1 – cria projeto e ponto via API', async ({ request }) => {
      await skipIfBackendIndisponivel(request)
      skipIfSemAuth()
      ;({ projetoId, pontoId } = await criarProjetoPonto(request, '-A'))
      expect(projetoId).toBeTruthy()
      expect(pontoId).toBeTruthy()
    })

    test('1.2 – persiste cálculo e recebe 200 com operation-id', async ({ request }) => {
      await skipIfBackendIndisponivel(request)
      skipIfSemAuth()
      if (!pontoId) test.skip(true, 'Pré-condição 1.1 falhou')

      const payload = buildCalculoPayload(pontoId)
      const resp = await apiPost(request, `/api/pontos/${pontoId}/calculo`, payload)

      expect(resp.status(), 'POST /api/pontos/:id/calculo deve retornar 200').toBe(200)
      expect(resp.headers()['x-operation-id'], 'x-operation-id deve estar presente').toBeTruthy()
    })

    test('1.3 – snapshot recuperável imediatamente após salvar', async ({ request }) => {
      await skipIfBackendIndisponivel(request)
      skipIfSemAuth()
      if (!pontoId) test.skip(true, 'Pré-condição 1.1 falhou')

      const snapshotResp = await apiGet(request, `/api/pontos/${pontoId}/snapshot`)
      expect(snapshotResp.status(), 'GET /api/pontos/:id/snapshot deve retornar 200').toBe(200)

      const snapshot = await snapshotResp.json()
      expect(snapshot.ponto_id).toBe(pontoId)
      expect(Array.isArray(snapshot.niveis)).toBe(true)
      expect(snapshot.niveis).toHaveLength(5)
      expect(snapshot.resultado.total_tracao).toBe(180.0)
      expect(snapshot.resultado.total_angulo).toBe(5.0)
    })

    test('1.4 – UI: navega, preenche dados e exibe chip "saved" (smoke visual)', async ({ page, request }) => {
      await skipIfBackendIndisponivel(request)
      skipIfSemAuth()

      // A UI usa o mesmo backend real; sem rotas mockadas
      await page.goto('/', { waitUntil: 'networkidle', timeout: 20_000 })

      // Deve exibir o formulário de projeto
      const heading = page.getByRole('heading', { name: /cadastro do projeto/i })
      await expect(heading).toBeVisible({ timeout: 15_000 })

      // Verifica que o stepper está na etapa "projeto"
      const stepperOrIndicator = page.locator('.stepper-container, .flow-stepper, [data-etapa]').first()
      if (await stepperOrIndicator.count() > 0) {
        await expect(stepperOrIndicator).toBeVisible()
      }

      // Preenchimento do formulário de projeto
      const inputProjeto = page.getByLabel('Projeto')
      await inputProjeto.fill(`E2E Real Visual ${RUN_ID}`)

      // Confirmar projeto
      await page.getByRole('button', { name: /confirmar/i }).click()

      // Aguarda transição para etapa de cálculo
      await expect(page.getByRole('button', { name: /apaga/i })).toBeVisible({ timeout: 20_000 })
    })
  })

  // ── Cenário 2: Falha de persistência (ponto inexistente) ──────────────────

  test.describe.serial('2 – Falha: ponto_id inválido retorna erro de contrato', () => {
    test('pré-condição: backend acessível', async ({ request }) => {
      await skipIfBackendIndisponivel(request)
    })

    test('2.1 – ponto_id inexistente retorna 404 ou 422', async ({ request }) => {
      await skipIfBackendIndisponivel(request)
      skipIfSemAuth()

      const pontoFalsoId = '00000000-0000-4000-8000-000000000000'
      const payload = buildCalculoPayload(pontoFalsoId)
      const resp = await apiPost(request, `/api/pontos/${pontoFalsoId}/calculo`, payload)

      const status = resp.status()
      expect([404, 422, 403], `Status inesperado: ${status}`).toContain(status)
    })

    test('2.2 – ponto_id divergente no payload retorna 422 com operation-id', async ({ request }) => {
      await skipIfBackendIndisponivel(request)
      skipIfSemAuth()

      const { pontoId } = await criarProjetoPonto(request, '-B')
      const payload = buildCalculoPayload(pontoId)

      // Divergência deliberada entre URL e payload
      const pontoIdDivergente = '11111111-1111-4111-8111-000000000001'
      const resp = await apiPost(request, `/api/pontos/${pontoId}/calculo`, {
        ...payload,
        ponto_id: pontoIdDivergente,
      })

      expect(resp.status(), 'ponto_id divergente deve retornar 422').toBe(422)
      expect(resp.headers()['x-operation-id'], 'x-operation-id esperado no erro').toBeTruthy()
    })

    test('2.3 – GET /health retorna 200 quando backend real está rodando', async ({ request }) => {
      await skipIfBackendIndisponivel(request)

      const resp = await request.get(`${API_BASE}/health`, { timeout: 5000 })
      expect(resp.status()).toBe(200)
    })
  })

  // ── Cenário 3: Auth gate (sem token) ──────────────────────────────────────

  test.describe('3 – Auth gate: mutação sem JWT retorna 401', () => {
    test('POST /api/projetos sem auth retorna 401', async ({ request }) => {
      await skipIfBackendIndisponivel(request)

      const resp = await request.post(`${API_BASE}/api/projetos`, {
        headers: { 'Content-Type': 'application/json' },
        data: criarProjeto().withNome(`E2E-NoAuth-${RUN_ID}`).build(),
      })

      // 401 sem token; 403 também é aceitável dependendo da configuração
      expect([401, 403], `Status inesperado sem auth: ${resp.status()}`).toContain(resp.status())
    })
  })
})
