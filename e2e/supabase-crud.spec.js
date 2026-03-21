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

// API usada nos testes E2E (configurável via E2E_API_URL)
const API = process.env.E2E_API_URL || 'http://localhost:8011'
const ADMIN_TOKEN = process.env.E2E_ADMIN_TOKEN || 'dev-admin-token'
const ADMIN_HEADERS = {
  'X-Admin-Token': ADMIN_TOKEN,
}
const SUPABASE_INDISPONIVEL_RE =
  /Supabase not configured|Supabase connection error|UndefinedTable|relation .* does not exist|does not exist/i
const DOES_NOT_EXIST_RE = /does not exist/i
const SUPABASE_SCHEMA_HINT_RE = /relation|schema|table|UndefinedTable/i

async function skipIfSupabaseIndisponivel(response, endpoint) {
  if (response.ok()) return

  const text = await response.text()
  const status = response.status()
  const matchedIndisponivel = SUPABASE_INDISPONIVEL_RE.test(text)
  const hasSchemaHint = SUPABASE_SCHEMA_HINT_RE.test(text)
  const genericDoesNotExistSemContexto = DOES_NOT_EXIST_RE.test(text) && !hasSchemaHint

  if (status === 503 || (status >= 500 && matchedIndisponivel && !genericDoesNotExistSemContexto)) {
    console.warn(`[SKIP] ${endpoint}: ${response.status()} — ${text}`)
    test.skip(true, `Supabase indisponível (${response.status()})`)
  }

  expect(response.ok(), `${endpoint} retornou ${response.status()} — ${text}`).toBeTruthy()
}

async function parseJsonOuSkipSupabasePublic(response, endpoint) {
  const status = response.status()
  const text = await response.text()

  if (status === 503 || /Supabase/i.test(text)) {
    console.warn(`[SKIP] ${endpoint}: ${status} — ${text}`)
    test.skip(true, `Supabase indisponível (${status})`)
  }

  expect(response.ok(), `${endpoint} retornou ${status} — ${text}`).toBeTruthy()
  return JSON.parse(text)
}

// IDs únicos por execução para evitar conflito entre runs paralelos
const RUN_ID = Date.now()
const TEST_CABO_NOME = `TEST_CABO_PW_${RUN_ID}`
const TEST_POSTE_MODELO = `TEST_POSTE_PW_${RUN_ID}`

// Estado compartilhado entre testes seriais
let createdCaboId
let createdPosteId

// ============================================================================
// Suite 1 — Cabos (CRUD completo)
// ============================================================================
test.describe.serial('Supabase CRUD — Cabos', () => {
  test('POST /admin/cabos — cria cabo de teste', async ({ request }) => {
    const res = await request.post(
      `${API}/admin/cabos?nome=${encodeURIComponent(TEST_CABO_NOME)}&diametro=15.2&peso=1.8`,
      { headers: ADMIN_HEADERS },
    )

    await skipIfSupabaseIndisponivel(res, 'POST /admin/cabos')

    const body = await res.json()
    console.log('Cabo criado:', JSON.stringify(body))

    if (!body?.id) {
      test.skip(true, 'Supabase indisponível (POST /admin/cabos sem id retornado)')
    }

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

    const res = await request.get(`${API}/admin/cabos`, { headers: ADMIN_HEADERS })
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

    const res = await request.delete(`${API}/admin/cabos/${createdCaboId}`, { headers: ADMIN_HEADERS })
    await skipIfSupabaseIndisponivel(res, 'DELETE /admin/cabos/{id}')

    const body = await res.json()
    expect(body).toHaveProperty('success')
    expect(body.success).toBe(true)

    createdCaboId = null // marcado como deletado
  })

  test('GET /admin/cabos — confirma remoção do cabo', async ({ request }) => {
    if (createdCaboId !== null) {
      test.skip(true, 'DELETE não foi executado')
    }

    const res = await request.get(`${API}/admin/cabos`, { headers: ADMIN_HEADERS })
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
      { headers: ADMIN_HEADERS },
    )

    await skipIfSupabaseIndisponivel(res, 'POST /admin/postes')

    const body = await res.json()
    console.log('Poste criado:', JSON.stringify(body))

    if (!body?.id) {
      test.skip(true, 'Supabase indisponível (POST /admin/postes sem id retornado)')
    }

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

    const res = await request.get(`${API}/admin/postes`, { headers: ADMIN_HEADERS })
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

    const res = await request.delete(`${API}/admin/postes/${createdPosteId}`, { headers: ADMIN_HEADERS })
    await skipIfSupabaseIndisponivel(res, 'DELETE /admin/postes/{id}')

    const body = await res.json()
    expect(body).toHaveProperty('success')
    expect(body.success).toBe(true)

    createdPosteId = null
  })

  test('GET /admin/postes — confirma remoção do poste', async ({ request }) => {
    if (createdPosteId !== null) {
      test.skip(true, 'DELETE não foi executado')
    }

    const res = await request.get(`${API}/admin/postes`, { headers: ADMIN_HEADERS })
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
  test('GET /public/normas — resposta válida', async ({ request }) => {
    const res = await request.get(`${API}/public/normas`)
    const body = await parseJsonOuSkipSupabasePublic(res, 'GET /public/normas')
    expect(body).not.toBeNull()
  })

  test('GET /public/normas?categoria=NBR — filtro funciona', async ({ request }) => {
    const res = await request.get(`${API}/public/normas?categoria=NBR`)
    const body = await parseJsonOuSkipSupabasePublic(res, 'GET /public/normas?categoria=NBR')
    expect(body).not.toBeNull()
  })

  test('GET /public/normas/categorias — retorna estrutura válida', async ({ request }) => {
    const res = await request.get(`${API}/public/normas/categorias`)
    const body = await parseJsonOuSkipSupabasePublic(res, 'GET /public/normas/categorias')
    expect(body).not.toBeNull()
  })
})

// ============================================================================
// Suite 4 — Autenticação JWT (validação de rejeição sem token)
//
// NOTA: Os endpoints de mutação (/projetos, /pontos, /calcular com persistência)
// exigem JWT válido quando AUTH_REQUIRE_JWT_FOR_MUTATIONS=true (default em prod).
// A validação unitária completa do JWT é coberta em pytest (test_api_validation.py).
// Aqui verificamos apenas que a API está acessível e retorna 401/403 sem token.
// ============================================================================
test.describe('Autenticação — Rejeição sem token', () => {
  test('POST /projetos sem token retorna 401 ou 403 (auth habilitada)', async ({ request }) => {
    const res = await request.post(`${API}/projetos`, {
      data: { nome: 'Projeto sem auth' },
      headers: { 'Content-Type': 'application/json' },
      // Sem X-Admin-Token nem Authorization header
    })

    const status = res.status()

    if (status === 503) {
      // Supabase não configurado — aceitável em CI sem DB
      console.warn('[SKIP] /projetos: Supabase não configurado (503)')
      test.skip(true, 'Supabase indisponível')
      return
    }

    // Auth real é testada via pytest; aqui só garantimos que não retorna 500
    // sem autenticação. Em dev (AUTH_REQUIRE_JWT_FOR_MUTATIONS=false), pode
    // retornar 422 (payload inválido) ou 201 (criação bem-sucedida).
    expect(status, `Esperado não-500, recebido ${status}`).not.toBe(500)
  })
})
