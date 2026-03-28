/* Tests for the pure helper functions exported from calculoApi.js:
 * buildCalculoRequest, buildBatchPayload, buildSalvarCalculoPayload,
 * extractSectionErrors
 * Also covers HTTP error parsing (403, 42501, Supabase format) via persistCalculo.
 * The private toFloat helper is indirectly exercised through these.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  buildCalculoRequest,
  buildBatchPayload,
  buildSalvarCalculoPayload,
  getLastRequestContext,
  extractSectionErrors,
  persistCalculo,
} from '@/services/calculoApi'

// ─── minimal form-state factory ──────────────────────────────────────────────
function makeTravessia(overrides = {}) {
  return {
    tipoRede: 'MT',
    tipoCabo: 'CAA 120',
    vao: '50',
    flecha: '1,2', // comma-decimal — toFloat must handle this
    angulo: '10',
    alturaPoste: '11',
    alturaAncoragem: '1',
    ...overrides,
  }
}

function makeBTZTravessia(overrides = {}) {
  return {
    qtdLigacoes: '4',
    vao: '30',
    flecha: '0.8',
    angulo: '0',
    alturaPoste: '9',
    alturaAncoragem: '0.5',
    ...overrides,
  }
}

function makeRALTravessia(overrides = {}) {
  return {
    tipoCabo: 'CAA 50',
    qtdCabos: '2',
    vao: '20',
    flecha: '0.5',
    angulo: '5',
    alturaPoste: '9',
    alturaAncoragem: '0.5',
    ...overrides,
  }
}

function makeFormState(overrides = {}) {
  return {
    cabecalho: {
      orgao: 'ANEEL',
      ns: 'NS-001',
      projeto: 'Projeto Teste',
      ponto: 'P1',
      endereco: 'Rua das Flores, 1',
      estudadoPor: 'Eng. Silva',
      matricula: '12345',
      data: '2024-01-01',
    },
    poste: {
      tipoPoste: 'DE-11/200',
      modeloPoste: 'Concreto',
    },
    mt1: [makeTravessia(), makeTravessia({ vao: '60', flecha: '1.5' })],
    mt2: [makeTravessia({ angulo: '20' })],
    bt: [makeTravessia({ tipoRede: 'BT' })],
    btz: [makeBTZTravessia()],
    ral: [makeRALTravessia()],
    ...overrides,
  }
}

function makeResultado(overrides = {}) {
  return {
    mt1: { tracao_dan: 120.5, angulo_graus: 10, texto: 'MT1 OK' },
    mt2: { tracao_dan: 80.0, angulo_graus: 20, texto: 'MT2 OK' },
    bt: { tracao_dan: 60.0, angulo_graus: 5, texto: 'BT OK' },
    btz: { tracao_dan: 30.0, angulo_graus: 0, texto: 'BTZ OK' },
    ral: { tracao_dan: 25.0, angulo_graus: 5, texto: 'RAL OK' },
    total_tracao_dan: 315.5,
    total_angulo_graus: 12,
    poste_ecc_dan: 200,
    texto_total: 'TOTAL OK',
    ...overrides,
  }
}

// ─── buildCalculoRequest ──────────────────────────────────────────────────────
describe('buildCalculoRequest', () => {
  it('maps cabecalho fields correctly', () => {
    const form = makeFormState()
    const req = buildCalculoRequest(form)

    expect(req.cabecalho).toMatchObject({
      orgao: 'ANEEL',
      ns: 'NS-001',
      projeto: 'Projeto Teste',
      ponto: 'P1',
      endereco: 'Rua das Flores, 1',
      estudado_por: 'Eng. Silva',
      matricula: '12345',
      data: '2024-01-01',
    })
  })

  it('maps poste fields correctly', () => {
    const req = buildCalculoRequest(makeFormState())
    expect(req.poste).toEqual({ tipo_poste: 'DE-11/200', modelo_poste: 'Concreto' })
  })

  it('converts comma-decimal strings to floats (toFloat)', () => {
    const req = buildCalculoRequest(makeFormState())
    // mt1[0].flecha was '1,2' — must become 1.2
    expect(req.mt1[0].flecha).toBe(1.2)
  })

  it('maps all MT1 travessias with correct fields', () => {
    const req = buildCalculoRequest(makeFormState())
    expect(req.mt1).toHaveLength(2)
    expect(req.mt1[0]).toMatchObject({
      tipo_rede: 'MT',
      tipo_cabo: 'CAA 120',
      vao: 50,
      flecha: 1.2,
      angulo: 10,
      altura_poste: 11,
      altura_ancoragem: 1,
    })
    expect(req.mt1[1].vao).toBe(60)
  })

  it('maps BTZ travessias with qtd_ligacoes', () => {
    const req = buildCalculoRequest(makeFormState())
    expect(req.btz[0]).toMatchObject({
      qtd_ligacoes: 4,
      vao: 30,
      flecha: 0.8,
    })
  })

  it('maps RAL travessias with qtd_cabos', () => {
    const req = buildCalculoRequest(makeFormState())
    expect(req.ral[0]).toMatchObject({
      tipo_cabo: 'CAA 50',
      qtd_cabos: 2,
      vao: 20,
    })
  })

  it('treats empty string values as null / 0', () => {
    const form = makeFormState({
      mt1: [makeTravessia({ vao: '', flecha: '', angulo: '' })],
    })
    const req = buildCalculoRequest(form)
    expect(req.mt1[0].vao).toBe(0)
    expect(req.mt1[0].flecha).toBe(0)
    expect(req.mt1[0].angulo).toBe(0)
  })

  it('accepts estudado_por (snake_case) in cabecalho', () => {
    const form = makeFormState()
    // Replace estudadoPor with snake_case variant
    form.cabecalho = { ...form.cabecalho, estudadoPor: undefined, estudado_por: 'Eng. Costa' }
    const req = buildCalculoRequest(form)
    expect(req.cabecalho.estudado_por).toBe('Eng. Costa')
  })
})

// ─── buildBatchPayload ────────────────────────────────────────────────────────
describe('buildBatchPayload', () => {
  it('includes projeto_id when provided', () => {
    const pid = '11111111-1111-1111-1111-111111111111'
    const payload = buildBatchPayload(pid, makeFormState(), makeResultado())
    expect(payload.projeto_id).toBe(pid)
    expect(payload.projeto_dados).toBeNull()
  })

  it('omits projeto_id and includes projeto_dados when not provided', () => {
    const payload = buildBatchPayload(null, makeFormState(), makeResultado())
    expect(payload.projeto_id).toBeNull()
    expect(payload.projeto_dados).toMatchObject({
      orgao: 'ANEEL',
      ns: 'NS-001',
      nome: 'Projeto Teste',
      endereco: 'Rua das Flores, 1',
      estudado_por: 'Eng. Silva',
      matricula: '12345',
      data_estudo: '2024-01-01',
    })
  })

  it('produces five level entries (MT1 MT2 BT BTZ RAL)', () => {
    const payload = buildBatchPayload('id-1', makeFormState(), makeResultado())
    const nivelNames = payload.niveis.map(n => n.nivel)
    expect(nivelNames).toEqual(['MT1', 'MT2', 'BT', 'BTZ', 'RAL'])
  })

  it('correctly maps resultado into payload', () => {
    const res = makeResultado()
    const payload = buildBatchPayload('id-1', makeFormState(), res)
    expect(payload.resultado).toMatchObject({
      mt1_tracao: 120.5,
      mt2_tracao: 80.0,
      bt_tracao: 60.0,
      btz_tracao: 30.0,
      ral_tracao: 25.0,
      total_tracao: 315.5,
      total_angulo: 12,
      poste_ecc: 200,
      texto_total: 'TOTAL OK',
    })
  })

  it('handles null resultado gracefully — all fields default to 0 / empty string', () => {
    const payload = buildBatchPayload('id-1', makeFormState(), null)
    expect(payload.resultado.mt1_tracao).toBe(0)
    expect(payload.resultado.total_tracao).toBe(0)
    expect(payload.resultado.texto_total).toBe('')
  })

  it('includes ponto_dados from cabecalho / poste', () => {
    const payload = buildBatchPayload('id-1', makeFormState(), makeResultado())
    expect(payload.ponto_dados).toEqual({
      ponto: 'P1',
      tipo_poste: 'DE-11/200',
      modelo_poste: 'Concreto',
    })
  })
})

// ─── buildSalvarCalculoPayload ────────────────────────────────────────────────
describe('buildSalvarCalculoPayload', () => {
  it('sets ponto_id correctly', () => {
    const pontoId = '33333333-3333-3333-3333-333333333333'
    const calculoReq = buildCalculoRequest(makeFormState())
    const payload = buildSalvarCalculoPayload(pontoId, calculoReq, makeResultado())
    expect(payload.ponto_id).toBe(pontoId)
  })

  it('produces five niveis with hoisted altura_poste from first travessia', () => {
    const calculoReq = buildCalculoRequest(makeFormState())
    const payload = buildSalvarCalculoPayload('p-id', calculoReq, makeResultado())

    expect(payload.niveis).toHaveLength(5)
    const mt1Nivel = payload.niveis.find(n => n.nivel === 'MT1')
    expect(mt1Nivel.altura_poste).toBe(11)
    expect(mt1Nivel.altura_ancoragem).toBe(1)
  })

  it('maps resultado using the same mapping as buildBatchPayload', () => {
    const res = makeResultado()
    const calculoReq = buildCalculoRequest(makeFormState())
    const payload = buildSalvarCalculoPayload('p-id', calculoReq, res)
    expect(payload.resultado.mt1_tracao).toBe(120.5)
    expect(payload.resultado.texto_mt1).toBe('MT1 OK')
  })

  it('includes posicao index (1-based) in each travessia entry', () => {
    const form = makeFormState({
      mt1: [makeTravessia(), makeTravessia({ vao: '80' }), makeTravessia({ vao: '90' })],
    })
    const calculoReq = buildCalculoRequest(form)
    const payload = buildSalvarCalculoPayload('p-id', calculoReq, makeResultado())
    const mt1Nivel = payload.niveis.find(n => n.nivel === 'MT1')
    expect(mt1Nivel.travessias[0].posicao).toBe(1)
    expect(mt1Nivel.travessias[1].posicao).toBe(2)
    expect(mt1Nivel.travessias[2].posicao).toBe(3)
  })
})

// ─── getLastRequestContext (initial state) ────────────────────────────────────
describe('getLastRequestContext', () => {
  it('returns a snapshot object (not the live reference)', () => {
    const ctx1 = getLastRequestContext()
    const ctx2 = getLastRequestContext()
    expect(ctx1).not.toBe(ctx2) // different object instances
    expect(ctx1).toEqual(ctx2)
  })

  it('starts with all-null fields on module initialisation', () => {
    const ctx = getLastRequestContext()
    expect(ctx.operation_id).toBeNull()
    expect(ctx.method).toBeNull()
    expect(ctx.url).toBeNull()
    expect(ctx.status).toBeNull()
  })
})

// ─── extractSectionErrors ─────────────────────────────────────────────────────
describe('extractSectionErrors', () => {
  it('returns null for non-array detail (string)', () => {
    expect(extractSectionErrors('Entrada fora do domínio')).toBeNull()
  })

  it('returns null for null/undefined', () => {
    expect(extractSectionErrors(null)).toBeNull()
    expect(extractSectionErrors(undefined)).toBeNull()
  })

  it('returns null for empty array', () => {
    expect(extractSectionErrors([])).toBeNull()
  })

  it('extracts mt1 error from Pydantic loc array', () => {
    const detail = [
      { loc: ['body', 'mt1', 0, 'vao'], msg: 'field required', type: 'value_error.missing' },
    ]
    const result = extractSectionErrors(detail)
    expect(result).toEqual({ mt1: 'field required' })
  })

  it('extracts errors for multiple sections', () => {
    const detail = [
      { loc: ['body', 'mt1', 0, 'vao'], msg: 'value is not a valid float' },
      { loc: ['body', 'bt', 1, 'flecha'], msg: 'field required' },
    ]
    const result = extractSectionErrors(detail)
    expect(result).toEqual({ mt1: 'value is not a valid float', bt: 'field required' })
  })

  it('joins multiple errors for the same section with semicolon', () => {
    const detail = [
      { loc: ['body', 'mt1', 0, 'vao'], msg: 'too small' },
      { loc: ['body', 'mt1', 1, 'flecha'], msg: 'too large' },
    ]
    const result = extractSectionErrors(detail)
    expect(result).toEqual({ mt1: 'too small; too large' })
  })

  it('ignores entries with unknown section keys', () => {
    const detail = [
      { loc: ['body', 'poste', 'tipo'], msg: 'invalid' },
    ]
    expect(extractSectionErrors(detail)).toBeNull()
  })

  it('ignores entries without loc array', () => {
    const detail = [
      { msg: 'some error' },
      { loc: 'not-an-array', msg: 'other error' },
    ]
    expect(extractSectionErrors(detail)).toBeNull()
  })

  it('is case-insensitive for section keys', () => {
    const detail = [
      { loc: ['body', 'MT1', 0, 'vao'], msg: 'error' },
    ]
    const result = extractSectionErrors(detail)
    expect(result).toEqual({ mt1: 'error' })
  })

  it('recognises all five section keys: mt1 mt2 bt btz ral', () => {
    const sections = ['mt1', 'mt2', 'bt', 'btz', 'ral']
    const detail = sections.map(s => ({ loc: ['body', s, 0, 'vao'], msg: `${s} error` }))
    const result = extractSectionErrors(detail)
    expect(Object.keys(result).sort()).toEqual(sections.sort())
  })
})

// ─── HTTP error parsing — 403 / 42501 / Supabase format ──────────────────────
describe('requestJson error parsing (via persistCalculo)', () => {
  const MOCK_URL = '/api/postes/1/calculo'

  function mockFetchResponse(status, body) {
    return vi.fn().mockResolvedValue({
      ok: false,
      status,
      statusText: 'Error',
      json: () => Promise.resolve(body),
      headers: { get: () => null },
      url: MOCK_URL,
    })
  }

  beforeEach(() => {
    vi.stubGlobal('fetch', mockFetchResponse(500, { detail: 'server error' }))
    // Provide the localStorage stub required by requestJson
    vi.stubGlobal('localStorage', { getItem: () => null })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('marks isForbidden for HTTP 403', async () => {
    vi.stubGlobal('fetch', mockFetchResponse(403, { detail: 'Forbidden' }))
    await expect(persistCalculo('1', {})).rejects.toMatchObject({
      status: 403,
      isForbidden: true,
      code: 'FORBIDDEN',
    })
  })

  it('marks isForbidden for Supabase 42501 code with HTTP 400', async () => {
    // Supabase/PostgREST may surface 42501 as a 400 with code in body
    vi.stubGlobal(
      'fetch',
      mockFetchResponse(400, { message: 'permission denied for table calculos', code: '42501' }),
    )
    await expect(persistCalculo('1', {})).rejects.toMatchObject({
      isForbidden: true,
      code: 'FORBIDDEN',
    })
  })

  it('extracts message from Supabase format (payload.message)', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetchResponse(403, { message: 'new row violates row-level security policy', code: '42501' }),
    )
    const err = await persistCalculo('1', {}).catch(e => e)
    expect(err.message).toBe('new row violates row-level security policy')
    expect(err.isForbidden).toBe(true)
  })

  it('does NOT mark isForbidden for unrelated 400 errors', async () => {
    vi.stubGlobal('fetch', mockFetchResponse(400, { detail: 'Bad request' }))
    const err = await persistCalculo('1', {}).catch(e => e)
    expect(err.isForbidden).toBeUndefined()
    expect(err.status).toBe(400)
  })
})
