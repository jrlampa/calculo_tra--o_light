/**
 * e2e/api-health.spec.js
 *
 * Smoke tests para a API FastAPI (porta 8000).
 * Usa o contexto `request` do Playwright — sem browser, só HTTP.
 *
 * Cobre:
 *   - GET  /health
 *   - GET  /admin/cabos   (fallback Excel se Supabase não configurado)
 *   - GET  /admin/postes  (idem)
 *   - GET  /admin/redes   (idem)
 *   - GET  /admin/normas/categorias
 *   - POST /calcular      com payload zerado → retorna total_tracao_dan = 0
 */
import { test, expect } from '@playwright/test'

// porta 8001: servidor atualizado com fallback Excel (8000 = servidor antigo, apenas Vite proxy)
const API = 'http://localhost:8001'

test.describe('API – Health & Lookup endpoints', () => {
  test('GET /health → {status: "ok"}', async ({ request }) => {
    const res = await request.get(`${API}/health`)
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body).toMatchObject({ status: 'ok' })
  })

  test('GET /admin/cabos → array não-vazio', async ({ request }) => {
    const res = await request.get(`${API}/admin/cabos`)
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(Array.isArray(body)).toBeTruthy()
    expect(body.length).toBeGreaterThan(0)
    // Cada item deve ter pelo menos a chave "nome"
    expect(body[0]).toHaveProperty('nome')
  })

  test('GET /admin/postes → array não-vazio', async ({ request }) => {
    const res = await request.get(`${API}/admin/postes`)
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(Array.isArray(body)).toBeTruthy()
    expect(body.length).toBeGreaterThan(0)
  })

  test('GET /admin/redes → array não-vazio', async ({ request }) => {
    const res = await request.get(`${API}/admin/redes`)
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(Array.isArray(body)).toBeTruthy()
    expect(body.length).toBeGreaterThan(0)
  })

  test('GET /admin/normas/categorias → resposta válida', async ({ request }) => {
    const res = await request.get(`${API}/admin/normas/categorias`)
    expect(res.ok()).toBeTruthy()
    // Retorna array (Supabase) ou objeto {categorias:[]} (fallback)
    const body = await res.json()
    expect(body).not.toBeNull()
  })

  test('POST /calcular com inputs zerados → total_tracao_dan = 0', async ({ request }) => {
    const payload = {
      cabecalho: {
        orgao: '', ns: '', projeto: '', ponto: '',
        endereco: '', estudado_por: '', matricula: '', data: '',
      },
      poste: {
        tipo_poste: 'Concreto',
        modelo_poste: 'CC / 11 m / 600 daN',
        carga_nominal: 600,
      },
      mt1: [], mt2: [], bt: [], btz: [], ral: [],
    }

    const res = await request.post(`${API}/calcular`, { data: payload })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()

    expect(body).toHaveProperty('total_tracao_dan')
    expect(body).toHaveProperty('mt1')
    expect(body).toHaveProperty('bt')
    expect(body).toHaveProperty('vetores')
    expect(body.total_tracao_dan).toBe(0)
  })

  test('POST /calcular com vão MT1 = 50 m → retorna tracao > 0', async ({ request }) => {
    const payload = {
      cabecalho: { orgao: 'TEST', ns: '', projeto: '', ponto: '1', endereco: '', estudado_por: '', matricula: '', data: '' },
      poste: { tipo_poste: 'Concreto', modelo_poste: 'CC / 11 m / 600 daN', carga_nominal: 600 },
      mt1: [
        {
          tipo_rede: 'Convencional',
          tipo_cabo: '397MCM-CA, Nu',
          vao: 50,
          flecha: 1.5,
          angulo: 0,
          altura_poste: 11,
          altura_ancoragem: 1,
        },
      ],
      mt2: [], bt: [], btz: [], ral: [],
    }

    const res = await request.post(`${API}/calcular`, { data: payload })
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    expect(body.mt1.tracao_dan).toBeGreaterThan(0)
    expect(body.total_tracao_dan).toBeGreaterThan(0)
  })
})
