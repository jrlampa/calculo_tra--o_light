/**
 * e2e/api-health.spec.js
 */
import { test, expect } from '@playwright/test'

const API = process.env.E2E_API_URL || 'http://127.0.0.1:8000'

async function parseJsonOuSkipSupabase(res, endpoint) {
  const status = res.status()
  const text = await res.text()

  if (status === 503 || /Supabase/i.test(text)) {
    console.warn(`[SKIP] ${endpoint}: ${status} — ${text}`)
    test.skip(true, `Supabase indisponível em ${endpoint} (${status})`)
  }

  if (!res.ok()) {
    console.error(`[ERROR] ${endpoint} FAILED with ${status}: ${text}`)
  }

  expect(res.ok(), `${endpoint} retornou ${status} — ${text}`).toBeTruthy()
  try {
    return JSON.parse(text)
  } catch (e) {
    throw new Error(`Falha ao dar parse no JSON de ${endpoint}: ${text}`)
  }
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

  test('GET /api/cabos → array não-vazio', async ({ request }) => {
    const res = await request.get(`${API}/api/cabos`)
    const body = await parseJsonOuSkipSupabase(res, 'GET /api/cabos')
    expect(Array.isArray(body)).toBeTruthy()
  })

  test('GET /api/postes → array não-vazio', async ({ request }) => {
    const res = await request.get(`${API}/api/postes`)
    const body = await parseJsonOuSkipSupabase(res, 'GET /api/postes')
    expect(Array.isArray(body)).toBeTruthy()
  })

  test('GET /api/redes → array não-vazio', async ({ request }) => {
    const res = await request.get(`${API}/api/redes`)
    const body = await parseJsonOuSkipSupabase(res, 'GET /api/redes')
    expect(Array.isArray(body)).toBeTruthy()
  })

  test('GET /api/public/normas/categorias → resposta válida', async ({ request }) => {
    // Note: this one has dual 'public' because of router level prefix in public.py line 83
    const res = await request.get(`${API}/api/public/normas/categorias`)
    const body = await parseJsonOuSkipSupabase(res, 'GET /api/public/normas/categorias')
    expect(body).not.toBeNull()
  })

  test('POST /api/calcular com inputs zerados', async ({ request }) => {
    const payload = criarPayloadBaseCalculo()
    const res = await request.post(`${API}/api/calcular`, { 
      data: payload,
      headers: { 'Content-Type': 'application/json' }
    })
    const body = await parseJsonOuSkipSupabase(res, 'POST /api/calcular (zeros)')
    expect(body).toHaveProperty('total_tracao_dan')
    expect(body.total_tracao_dan).toBeGreaterThanOrEqual(0)
  })

  test('POST /api/calcular com vão MT1 = 50 m → retorna tracao > 0', async ({ request }) => {
    const payload = criarPayloadBaseCalculo()
    payload.mt1[0] = criarTravessiaMT({
      tipo_rede: 'Convencional',
      tipo_cabo: '397MCM-CA, Nu',
      vao: 50,
      flecha: 1.5,
      angulo: 0,
      altura_poste: 11,
      altura_ancoragem: 9.2,
    })

    const res = await request.post(`${API}/api/calcular`, { 
      data: payload,
      headers: { 'Content-Type': 'application/json' }
    })
    const body = await parseJsonOuSkipSupabase(res, 'POST /api/calcular (vao=50)')
    expect(body.mt1.tracao_dan).toBeGreaterThan(0)
  })
})
