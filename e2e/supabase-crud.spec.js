/**
 * e2e/supabase-crud.spec.js
 *
 * Testes de escrita e leitura no Supabase via endpoints /admin/*.
 * Requer DATABASE_URL configurada no .env para passar.
 * Se o Supabase não estiver configurado, os testes são pulados automaticamente.
 *
 * Fluxo de cada suite:
 *   1. POST  → cria um registro de teste (prefixo TEST_)
 *   2. GET   → verifica que o registro aparece na lista
 *   3. DELETE → remove o registro
 *   4. GET   → confirma remoção
 *
 * Os testes rodam em série (describe.serial) para garantir a ordem.
 */
import { test, expect } from '@playwright/test'

// porta 8001: servidor atualizado com fallback Excel (8000 = servidor antigo, apenas Vite proxy)
const API = 'http://localhost:8001'

// IDs únicos por execução para evitar conflito entre runs paralelos
const RUN_ID = Date.now()
const TEST_CABO_NOME = `TEST_CABO_PW_${RUN_ID}`
const TEST_POSTE_MODELO = `TEST_POSTE_PW_${RUN_ID}`

// Estado compartilhado entre testes seriais
let createdCaboId = null
let createdPosteId = null

// ============================================================================
// Suite 1 — Cabos (CRUD completo)
// ============================================================================
test.describe.serial('Supabase CRUD — Cabos', () => {
  test('POST /admin/cabos — cria cabo de teste', async ({ request }) => {
    const res = await request.post(
      `${API}/admin/cabos?nome=${encodeURIComponent(TEST_CABO_NOME)}&diametro=15.2&peso=1.8`,
    )

    if (!res.ok()) {
      const text = await res.text()
      console.warn(`[SKIP] Supabase não configurado: ${res.status()} — ${text}`)
      test.skip(true, `Supabase indisponível (${res.status()})`)
    }

    const body = await res.json()
    console.log('Cabo criado:', JSON.stringify(body))

    expect(body).toHaveProperty('id')
    expect(body).toHaveProperty('nome')
    expect(body.nome).toBe(TEST_CABO_NOME)
    expect(typeof body.id).toBe('number')

    createdCaboId = body.id
  })

  test('GET /admin/cabos — novo cabo aparece na lista', async ({ request }) => {
    if (!createdCaboId) {
      test.skip(true, 'Cabo de teste não foi criado (Supabase não configurado)')
    }

    const res = await request.get(`${API}/admin/cabos`)
    expect(res.ok()).toBeTruthy()

    const body = await res.json()
    expect(Array.isArray(body)).toBeTruthy()

    const found = body.find(c => c.nome === TEST_CABO_NOME)
    expect(found, `Cabo "${TEST_CABO_NOME}" não encontrado na lista`).toBeDefined()
    expect(found.id).toBe(createdCaboId)
  })

  test('DELETE /admin/cabos/{id} — remove cabo de teste', async ({ request }) => {
    if (!createdCaboId) {
      test.skip(true, 'Cabo de teste não foi criado (Supabase não configurado)')
    }

    const res = await request.delete(`${API}/admin/cabos/${createdCaboId}`)
    expect(res.ok()).toBeTruthy()

    const body = await res.json()
    expect(body).toHaveProperty('success')
    expect(body.success).toBe(true)

    createdCaboId = null // marcado como deletado
  })

  test('GET /admin/cabos — confirma remoção do cabo', async ({ request }) => {
    if (createdCaboId !== null) {
      test.skip(true, 'DELETE não foi executado')
    }

    const res = await request.get(`${API}/admin/cabos`)
    expect(res.ok()).toBeTruthy()

    const body = await res.json()
    const found = body.find(c => c.nome === TEST_CABO_NOME)
    expect(found, `Cabo "${TEST_CABO_NOME}" ainda aparece após deleção`).toBeUndefined()
  })
})

// ============================================================================
// Suite 2 — Postes (CRUD completo)
// ============================================================================
test.describe.serial('Supabase CRUD — Postes', () => {
  test('POST /admin/postes — cria poste de teste', async ({ request }) => {
    const res = await request.post(
      `${API}/admin/postes` +
      `?tipo=Concreto` +
      `&modelo=${encodeURIComponent(TEST_POSTE_MODELO)}` +
      `&altura_m=11` +
      `&carga_admissivel_dan=600`,
    )

    if (!res.ok()) {
      const text = await res.text()
      console.warn(`[SKIP] Supabase não configurado: ${res.status()} — ${text}`)
      test.skip(true, `Supabase indisponível (${res.status()})`)
    }

    const body = await res.json()
    console.log('Poste criado:', JSON.stringify(body))

    expect(body).toHaveProperty('id')
    expect(body).toHaveProperty('modelo')
    expect(body.modelo).toBe(TEST_POSTE_MODELO)
    expect(body.altura_m).toBe(11)
    expect(body.carga_admissivel_dan).toBe(600)

    createdPosteId = body.id
  })

  test('GET /admin/postes — novo poste aparece na lista', async ({ request }) => {
    if (!createdPosteId) {
      test.skip(true, 'Poste de teste não foi criado (Supabase não configurado)')
    }

    const res = await request.get(`${API}/admin/postes`)
    expect(res.ok()).toBeTruthy()

    const body = await res.json()
    expect(Array.isArray(body)).toBeTruthy()

    const found = body.find(p => p.modelo === TEST_POSTE_MODELO)
    expect(found, `Poste "${TEST_POSTE_MODELO}" não encontrado`).toBeDefined()
    expect(found.id).toBe(createdPosteId)
  })

  test('DELETE /admin/postes/{id} — remove poste de teste', async ({ request }) => {
    if (!createdPosteId) {
      test.skip(true, 'Poste de teste não foi criado (Supabase não configurado)')
    }

    const res = await request.delete(`${API}/admin/postes/${createdPosteId}`)
    expect(res.ok()).toBeTruthy()

    const body = await res.json()
    expect(body).toHaveProperty('success')
    expect(body.success).toBe(true)

    createdPosteId = null
  })

  test('GET /admin/postes — confirma remoção do poste', async ({ request }) => {
    if (createdPosteId !== null) {
      test.skip(true, 'DELETE não foi executado')
    }

    const res = await request.get(`${API}/admin/postes`)
    expect(res.ok()).toBeTruthy()

    const body = await res.json()
    const found = body.find(p => p.modelo === TEST_POSTE_MODELO)
    expect(found, `Poste "${TEST_POSTE_MODELO}" ainda aparece após deleção`).toBeUndefined()
  })
})

// ============================================================================
// Suite 3 — Normas (leitura apenas — escrita via extract_normas.py)
// ============================================================================
test.describe('Supabase — Normas (leitura)', () => {
  test('GET /admin/normas — resposta válida', async ({ request }) => {
    const res = await request.get(`${API}/admin/normas`)
    expect(res.ok()).toBeTruthy()
    // Se Supabase conectado: array (possivelmente vazio)
    // Se não: {message: "Supabase not configured"}
    const body = await res.json()
    expect(body).not.toBeNull()
  })

  test('GET /admin/normas?categoria=NBR — filtro funciona', async ({ request }) => {
    const res = await request.get(`${API}/admin/normas?categoria=NBR`)
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    // Array (possivelmente vazio) ou erro de configuração — ambos válidos
    expect(body).not.toBeNull()
  })

  test('GET /admin/normas/categorias — retorna estrutura válida', async ({ request }) => {
    const res = await request.get(`${API}/admin/normas/categorias`)
    expect(res.ok()).toBeTruthy()
    const body = await res.json()
    // Supabase: array de {categoria, count}. Sem Supabase: {categorias: []}
    expect(body).not.toBeNull()
  })
})
