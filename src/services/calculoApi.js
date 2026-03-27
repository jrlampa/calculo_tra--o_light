/**
 * The above code contains various functions for handling API requests and data mapping in a JavaScript
 * application.
 * @param value - The code you provided contains various functions related to handling JSON data,
 * parsing error messages, making API requests, and mapping data objects. It also includes functions
 * for building payloads and interacting with a backend API.
 * @returns The code provided includes various functions related to handling API requests, parsing
 * data, and mapping objects. The functions are related to creating, updating, and deleting projects
 * and points, as well as persisting calculations and listing projects. The code also includes
 * functions for building payloads and mapping data for calculations.
 */
const JSON_HEADERS = { 'Content-Type': 'application/json' }
const GUEST_HEADERS = { ...JSON_HEADERS, 'X-Guest-Access': 'true' }
const OPERATION_ID_HEADER = 'X-Operation-ID'

let lastRequestContext = {
  operation_id: null,
  method: null,
  url: null,
  status: null,
}

function storeRequestContext(response, url, method) {
  lastRequestContext = {
    operation_id: response.headers.get(OPERATION_ID_HEADER),
    method,
    url,
    status: response.status,
  }
}

export function getLastRequestContext() {
  return { ...lastRequestContext }
}

function toFloat(value) {
  if (value === '' || value === null || value === undefined) return null
  if (typeof value === 'number') return Number.isNaN(value) ? null : value
  const normalizedValue = String(value).replace(',', '.')
  const parsedValue = parseFloat(normalizedValue)
  return Number.isNaN(parsedValue) ? null : parsedValue
}

// Section keys as returned by the /calcular endpoint's Pydantic model
const SECAO_KEYS = new Set(['mt1', 'mt2', 'bt', 'btz', 'ral'])

/**
 * Parses a FastAPI Pydantic 422 `detail` array and groups error messages by
 * section key (mt1, mt2, bt, btz, ral). Returns null when no field-level
 * information is available (e.g. a plain string detail).
 *
 * @param {unknown} detail - The `detail` value from the 422 JSON body.
 * @returns {Record<string,string>|null} Map of section → joined error messages,
 *   or null if not a Pydantic-style validation error.
 */
export function extractSectionErrors(detail) {
  if (!Array.isArray(detail) || detail.length === 0) { return null }

  const bySection = {}
  for (const item of detail) {
    if (!item || !Array.isArray(item.loc) || item.loc.length < 2) { continue }
    // FastAPI loc format: ["body", "<field>", ...] or ["body", "<section>", <idx>, "<field>", ...]
    const rawKey = String(item.loc[1] || '').toLowerCase()
    if (!SECAO_KEYS.has(rawKey)) { continue }
    const msg = item.msg || 'Erro de validação'
    bySection[rawKey] = bySection[rawKey] ? `${bySection[rawKey]}; ${msg}` : msg
  }

  return Object.keys(bySection).length > 0 ? bySection : null
}

async function parseErrorMessage(response, fallbackMessage) {
  try {
    const payload = await response.json()
    if (typeof payload?.detail === 'string' && payload.detail) {
      return payload.detail
    }
    if (Array.isArray(payload?.detail) && payload.detail.length > 0) {
      return payload.detail.map(item => item?.msg || 'Erro de validação').join(', ')
    }
  } catch {
    return fallbackMessage
  }

  return fallbackMessage
}

async function requestJson(url, options = {}, fallbackMessage) {
  const method = options.method || 'GET'
  const response = await fetch(url, {
    credentials: 'include',
    ...options,
    headers: {
      ...options.headers,
      ...(window.localStorage.getItem('guest_mode') === 'true' ? GUEST_HEADERS : {})
    }
  })

  storeRequestContext(response, url, method)

  if (!response.ok) {
    const message = await parseErrorMessage(response, fallbackMessage)
    // Criar erro com status capturado (importante para diferenciar erros de autorização)
    const err = new Error(message)
    err.status = response.status
    err.statusText = response.statusText
    // Detectar código de autorização via mensagem de erro ou status
    if (response.status === 403 || message?.includes('permission') || message?.includes('authorized')) {
      err.code = 'FORBIDDEN'
      err.isForbidden = true
    }
    err.operationId = lastRequestContext.operation_id
    throw err
  }

  if (response.status === 204) return null
  return response.json()
}

function mapCabecalho(cabecalho) {
  return {
    orgao: cabecalho.orgao || '',
    ns: cabecalho.ns || '',
    projeto: cabecalho.projeto || '',
    ponto: cabecalho.ponto || '',
    endereco: cabecalho.endereco || '',
    estudado_por: cabecalho.estudado_por || cabecalho.estudadoPor || '',
    matricula: cabecalho.matricula || '',
    data: cabecalho.data || '',
  }
}

function mapPoste(poste) {
  return {
    tipo_poste: poste.tipoPoste || '',
    modelo_poste: poste.modeloPoste || '',
  }
}

function mapMTTravessia(travessia) {
  return {
    tipo_rede: travessia.tipoRede || '',
    tipo_cabo: travessia.tipoCabo || '',
    vao: toFloat(travessia.vao) ?? 0,
    flecha: toFloat(travessia.flecha) ?? 0,
    angulo: toFloat(travessia.angulo) ?? 0,
    altura_poste: toFloat(travessia.alturaPoste) ?? 0,
    altura_ancoragem: toFloat(travessia.alturaAncoragem) ?? 0,
  }
}

function mapBTTravessia(travessia) {
  return {
    tipo_rede: travessia.tipoRede || '',
    tipo_cabo: travessia.tipoCabo || '',
    vao: toFloat(travessia.vao) ?? 0,
    flecha: toFloat(travessia.flecha) ?? 0,
    angulo: toFloat(travessia.angulo) ?? 0,
    altura_poste: toFloat(travessia.alturaPoste) ?? 0,
    altura_ancoragem: toFloat(travessia.alturaAncoragem) ?? 0,
  }
}

function mapBTZTravessia(travessia) {
  return {
    qtd_ligacoes: toFloat(travessia.qtdLigacoes) ?? 0,
    vao: toFloat(travessia.vao) ?? 0,
    flecha: toFloat(travessia.flecha) ?? 0,
    angulo: toFloat(travessia.angulo) ?? 0,
    altura_poste: toFloat(travessia.alturaPoste) ?? 0,
    altura_ancoragem: toFloat(travessia.alturaAncoragem) ?? 0,
  }
}

function mapRALTravessia(travessia) {
  return {
    tipo_cabo: travessia.tipoCabo || '',
    qtd_cabos: toFloat(travessia.qtdCabos) ?? 0,
    vao: toFloat(travessia.vao) ?? 0,
    flecha: toFloat(travessia.flecha) ?? 0,
    angulo: toFloat(travessia.angulo) ?? 0,
    altura_poste: toFloat(travessia.alturaPoste) ?? 0,
    altura_ancoragem: toFloat(travessia.alturaAncoragem) ?? 0,
  }
}

function buildNivelPayload(nivel, travessias) {
  const primeiraTravessia = travessias[0] || {}

  return {
    nivel,
    altura_poste: primeiraTravessia.altura_poste ?? 0,
    altura_ancoragem: primeiraTravessia.altura_ancoragem ?? 0,
    travessias: travessias.map((travessia, index) => {
      const vao = travessia.vao ?? 0
      const flecha = travessia.flecha ?? 0

      if (vao > 0 && flecha <= 0) {
        console.warn(
          `[buildNivelPayload] Nível ${nivel}, posição ${index + 1}: flecha deve ser maior que zero quando vão é ${vao} m`
        )
      }

      return {
        posicao: index + 1,
        tipo_rede: travessia.tipo_rede ?? '',
        tipo_cabo: travessia.tipo_cabo ?? '',
        vao,
        flecha,
        angulo: travessia.angulo ?? 0,
        qtd_ligacoes: travessia.qtd_ligacoes ?? 0,
        qtd_cabos: travessia.qtd_cabos ?? 0,
      }
    }),
  }
}

function mapResultado(resultado) {
  return {
    mt1_tracao: resultado?.mt1?.tracao_dan ?? 0,
    mt1_angulo: resultado?.mt1?.angulo_graus ?? 0,
    mt2_tracao: resultado?.mt2?.tracao_dan ?? 0,
    mt2_angulo: resultado?.mt2?.angulo_graus ?? 0,
    bt_tracao: resultado?.bt?.tracao_dan ?? 0,
    bt_angulo: resultado?.bt?.angulo_graus ?? 0,
    btz_tracao: resultado?.btz?.tracao_dan ?? 0,
    btz_angulo: resultado?.btz?.angulo_graus ?? 0,
    ral_tracao: resultado?.ral?.tracao_dan ?? 0,
    ral_angulo: resultado?.ral?.angulo_graus ?? 0,
    total_tracao: resultado?.total_tracao_dan ?? 0,
    total_angulo: resultado?.total_angulo_graus ?? 0,
    poste_ecc: resultado?.poste_ecc_dan ?? 0,
    texto_mt1: resultado?.mt1?.texto ?? '',
    texto_mt2: resultado?.mt2?.texto ?? '',
    texto_bt: resultado?.bt?.texto ?? '',
    texto_btz: resultado?.btz?.texto ?? '',
    texto_ral: resultado?.ral?.texto ?? '',
    texto_total: resultado?.texto_total ?? '',
  }
}

export function buildCalculoRequest(formState) {
  const { cabecalho, poste, mt1, mt2, bt, btz, ral } = formState

  return {
    cabecalho: mapCabecalho(cabecalho),
    poste: mapPoste(poste),
    mt1: mt1.map(mapMTTravessia),
    mt2: mt2.map(mapMTTravessia),
    bt: bt.map(mapBTTravessia),
    btz: btz.map(mapBTZTravessia),
    ral: ral.map(mapRALTravessia),
  }
}

export function buildSalvarCalculoPayload(pontoId, calculoRequest, resultado) {
  return {
    ponto_id: pontoId,
    niveis: [
      buildNivelPayload('MT1', calculoRequest.mt1),
      buildNivelPayload('MT2', calculoRequest.mt2),
      buildNivelPayload('BT', calculoRequest.bt),
      buildNivelPayload('BTZ', calculoRequest.btz),
      buildNivelPayload('RAL', calculoRequest.ral),
    ],
    resultado: mapResultado(resultado),
  }
}

export function buildBatchPayload(projetoId, formState, resultado) {
  const { cabecalho, poste, mt1, mt2, bt, btz, ral } = formState

  return {
    projeto_id: projetoId || null,
    projeto_dados: !projetoId
      ? {
          orgao: cabecalho.orgao || '',
          ns: cabecalho.ns || '',
          nome: cabecalho.projeto || '',
          endereco: cabecalho.endereco || '',
          estudado_por: cabecalho.estudado_por || cabecalho.estudadoPor || '',
          matricula: cabecalho.matricula || '',
          data_estudo: cabecalho.data || '',
        }
      : null,
    ponto_dados: {
      ponto: cabecalho.ponto || '',
      tipo_poste: poste.tipoPoste || '',
      modelo_poste: poste.modeloPoste || '',
    },
    niveis: [
      buildNivelPayload('MT1', mt1.map(mapMTTravessia)),
      buildNivelPayload('MT2', mt2.map(mapMTTravessia)),
      buildNivelPayload('BT', bt.map(mapBTTravessia)),
      buildNivelPayload('BTZ', btz.map(mapBTZTravessia)),
      buildNivelPayload('RAL', ral.map(mapRALTravessia)),
    ],
    resultado: mapResultado(resultado),
  }
}

export async function createProjeto(cabecalho) {
  return requestJson(
    '/api/projetos',
    {
      method: 'POST',
      headers: JSON_HEADERS,
      body: JSON.stringify({
        orgao: cabecalho.orgao || '',
        ns: cabecalho.ns || '',
        nome: cabecalho.projeto || '',
        endereco: cabecalho.endereco || '',
        estudado_por: cabecalho.estudado_por || cabecalho.estudadoPor || '',
        matricula: cabecalho.matricula || '',
        data_estudo: cabecalho.data || '',
      }),
    },
    'Erro ao criar projeto'
  )
}

export async function createPonto(projetoId, dadosPonto) {
  return requestJson(
    `/api/projetos/${projetoId}/pontos`,
    {
      method: 'POST',
      headers: JSON_HEADERS,
      body: JSON.stringify({
        ponto: dadosPonto.ponto || '',
        tipo_poste: dadosPonto.tipoPoste || '',
        modelo_poste: dadosPonto.modeloPoste || '',
      }),
    },
    'Erro ao criar ponto'
  )
}

export async function persistCalculo(pontoId, payload) {
  return requestJson(
    `/api/pontos/${pontoId}/calculo`,
    {
      method: 'POST',
      headers: JSON_HEADERS,
      body: JSON.stringify(payload),
    },
    'Erro ao persistir cálculo'
  )
}

export async function listProjetos(limit = 20, offset = 0) {
  return requestJson(
    `/api/projetos?limit=${limit}&offset=${offset}`,
    { method: 'GET', headers: JSON_HEADERS },
    'Erro ao listar projetos'
  )
}

export async function updateProjeto(id, cabecalho) {
  return requestJson(
    `/api/projetos/${id}`,
    {
      method: 'PUT',
      headers: JSON_HEADERS,
      body: JSON.stringify({
        orgao: cabecalho.orgao,
        ns: cabecalho.ns,
        nome: cabecalho.projeto,
        endereco: cabecalho.endereco,
        estudado_por: cabecalho.estudado_por || cabecalho.estudadoPor,
        matricula: cabecalho.matricula,
        data_estudo: cabecalho.data,
      }),
    },
    'Erro ao atualizar projeto'
  )
}

export async function deleteProjeto(id) {
  return requestJson(
    `/api/projetos/${id}`,
    { method: 'DELETE', headers: JSON_HEADERS },
    'Erro ao excluir projeto'
  )
}

export async function batchSaveCalculo(payload) {
  return requestJson(
    '/api/projetos/batch-save',
    {
      method: 'POST',
      headers: JSON_HEADERS,
      body: JSON.stringify(payload),
    },
    'Erro ao realizar salvamento atômico'
  )
}