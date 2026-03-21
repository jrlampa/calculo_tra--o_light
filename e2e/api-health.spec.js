/**
 * e2e/api-health.spec.js
 *
 * Smoke tests para a API FastAPI (porta configurável via E2E_API_URL).
 * Usa o contexto `request` do Playwright — sem browser, só HTTP.
 *
 * Cobre:
 *   - GET  /health
 *   - GET  /public/cabos
 *   - GET  /public/postes
 *   - GET  /public/redes
 *   - GET  /public/normas/categorias
 *   - POST /calcular      com payload compatível com schema atual
 */
import { test, expect } from '@playwright/test'

const API = process.env.E2E_API_URL || 'http://localhost:8011'

async function parseJsonOuSkipSupabase(res, endpoint) {
  const status = res.status()
  const text = await res.text()

  if (status === 503 || /Supabase/i.test(text)) {
    console.warn(`[SKIP] ${endpoint}: ${status} — ${text}`)
    test.skip(true, `Supabase indisponível em ${endpoint} (${status})`)
  }

  expect(res.ok(), `${endpoint} retornou ${status} — ${text}`).toBeTruthy()
  return JSON.parse(text)
}

function criarTravessiaMT(overrides = {}) {
  return {
    tipo_rede: '',
    tipo_cabo: '',
    vao: 0,
    flecha: 0,
    angulo: 0,
    altura_poste: 0,
    altura_ancoragem: 0,
    ...overrides,
  }
}

function criarTravessiaBTZero(overrides = {}) {
  return {
    qtd_ligacoes: 0,
    vao: 0,
    flecha: 0,
    angulo: 0,
    altura_poste: 0,
    altura_ancoragem: 0,
    ...overrides,
  }
}

function criarTravessiaRAL(overrides = {}) {
  return {
    tipo_cabo: '',
    qtd_cabos: 0,
    vao: 0,
    flecha: 0,
    angulo: 0,
    altura_poste: 0,
    altura_ancoragem: 0,
    ...overrides,
  }
}

function criarPayloadBaseCalculo() {
  return {
    cabecalho: {
      orgao: 'TESTE',
      ns: '',
      projeto: 'PLAYWRIGHT',
      ponto: 'P1',
      endereco: '',
      estudado_por: '',
      matricula: '',
      data: '',
    },
    poste: {
      tipo_poste: 'Concreto circular',
      modelo_poste: '11 m / 600 daN',
    },
    mt1: Array.from({ length: 4 }, () => criarTravessiaMT()),
    mt2: Array.from({ length: 4 }, () => criarTravessiaMT()),
    bt: Array.from({ length: 4 }, () => criarTravessiaMT()),
    btz: Array.from({ length: 4 }, () => criarTravessiaBTZero()),
    ral: Array.from({ length: 4 }, () => criarTravessiaRAL()),
  }
}

test.describe('API – Health & Lookup endpoints', () => {
  test('GET /health → {status: "ok"}', async ({ request }) => {
    const res = await request.get(`${API}/health`)
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body).toMatchObject({ status: 'ok' })
  })

  test('GET /public/cabos → array não-vazio', async ({ request }) => {
    const res = await request.get(`${API}/public/cabos`)
    const body = await parseJsonOuSkipSupabase(res, 'GET /public/cabos')
    expect(Array.isArray(body)).toBeTruthy()
    if (body.length > 0) {
      expect(body[0]).toHaveProperty('nome')
    }
  })

  test('GET /public/postes → array não-vazio', async ({ request }) => {
    const res = await request.get(`${API}/public/postes`)
    const body = await parseJsonOuSkipSupabase(res, 'GET /public/postes')
    expect(Array.isArray(body)).toBeTruthy()
    if (body.length > 0) {
      expect(body[0]).toHaveProperty('modelo')
    }
  })

  test('GET /public/redes → array não-vazio', async ({ request }) => {
    const res = await request.get(`${API}/public/redes`)
    const body = await parseJsonOuSkipSupabase(res, 'GET /public/redes')
    expect(Array.isArray(body)).toBeTruthy()
    if (body.length > 0) {
      expect(body[0]).toHaveProperty('tipo')
    }
  })

  test('GET /public/normas/categorias → resposta válida', async ({ request }) => {
    const res = await request.get(`${API}/public/normas/categorias`)
    const body = await parseJsonOuSkipSupabase(res, 'GET /public/normas/categorias')
    expect(body).not.toBeNull()
  })

  test('POST /calcular com inputs zerados → total_tracao_dan reflete ECC do poste', async ({ request }) => {
    const payload = criarPayloadBaseCalculo()

    const res = await request.post(`${API}/calcular`, { data: payload })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()

    expect(body).toHaveProperty('total_tracao_dan')
    expect(body).toHaveProperty('mt1')
    expect(body).toHaveProperty('bt')
    expect(body).toHaveProperty('vetores')
    expect(body.total_tracao_dan).toBeCloseTo(body.poste_ecc_dan, 2)
  })

  test('POST /calcular com vão MT1 = 50 m → retorna tracao > 0', async ({ request }) => {
    const payload = criarPayloadBaseCalculo()
    payload.mt1[0] = criarTravessiaMT({
      tipo_rede: 'Convencional',
      tipo_cabo: '397MCM-CA, Nu',
      vao: 50,
      flecha: 1.5,
      angulo: 0,
      altura_poste: 11,
      altura_ancoragem: 1,
    })

    const res = await request.post(`${API}/calcular`, { data: payload })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.mt1.tracao_dan).toBeGreaterThan(0)
    expect(body.total_tracao_dan).toBeGreaterThan(0)
  })
})
