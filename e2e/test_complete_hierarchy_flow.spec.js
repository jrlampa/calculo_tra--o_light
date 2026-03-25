import { test, expect } from '@playwright/test';
import { criarProjeto, criarPonto, criarTravessia, criarResultado, criarCalculoPayload } from './helpers/test_factories.js';

const API_BASE_URL = process.env.API_URL || 'http://localhost:8000/api';
const ADMIN_TOKEN = process.env.X_ADMIN_TOKEN || 'test-token-for-development';
const GUEST_HEADER_NAME = process.env.E2E_GUEST_HEADER_NAME;
const GUEST_HEADER_VALUE = process.env.E2E_GUEST_HEADER_VALUE;
const LEVELS = ['MT1', 'MT2', 'BT', 'BTZ', 'RAL'];

function buildHeaders() {
  const headers = {
    'Content-Type': 'application/json',
    'X-Admin-Token': ADMIN_TOKEN,
  };

  if (GUEST_HEADER_NAME && GUEST_HEADER_VALUE) {
    headers[GUEST_HEADER_NAME] = GUEST_HEADER_VALUE;
  }

  return headers;
}

function buildTravessias(overrides = {}) {
  return [1, 2, 3, 4].map((posicao) => {
    const custom = overrides[posicao] || {};
    return criarTravessia(posicao)
      .withTipoRede(custom.tipo_rede ?? '')
      .withTipoCabo(custom.tipo_cabo ?? '')
      .withVao(custom.vao ?? 0)
      .withFlecha(custom.flecha ?? 0)
      .withAngulo(custom.angulo ?? 0)
      .withQtdLigacoes(custom.qtd_ligacoes ?? 0)
      .withQtdCabos(custom.qtd_cabos ?? 0)
      .build();
  });
}

function buildProjetoPayload(runId, isBatch = false) {
  const builder = criarProjeto()
    .withOrgao(isBatch ? 'TEST_BATCH_ORG' : 'TEST_ORGAO')
    .withNs(isBatch ? `NS-BATCH-${runId}` : `NS-${runId}`)
    .withNome(isBatch ? `BatchProjeto${runId}` : `TestProjeto${runId}`)
    .withEndereco(isBatch ? 'Rua Batch, 456' : 'Rua Teste, 123')
    .withEstudadoPor(isBatch ? 'E2E Batch Bot' : 'E2E Bot')
    .withMatricula(isBatch ? '8888' : '9999');

  if (!isBatch) {
    builder.withDataEstudo(new Date().toLocaleDateString('pt-BR'));
  }

  return builder.build();
}

function buildPontoPayload(runId, prefixo = 'P') {
  return criarPonto()
    .withRunId(runId, prefixo)
    .withTipoPoste('DT')
    .withModeloPoste('11/600')
    .build();
}

function buildResultado(payload) {
  return criarResultado()
    .withMt1Tracao(payload.mt1_tracao)
    .withMt1Angulo(payload.mt1_angulo)
    .withTotalTracao(payload.total_tracao)
    .withTotalAngulo(payload.total_angulo)
    .withPosteEcc(payload.poste_ecc)
    .withTextoMt1(payload.texto_mt1)
    .withTextoTotal(payload.texto_total)
    .build();
}

function buildSnapshotPayload(pontoId) {
  return criarCalculoPayload()
    .forPonto(pontoId)
    .withNivelMT1(
      buildTravessias({
        1: { tipo_rede: 'Convencional', tipo_cabo: '397MCM-CA, Nu', vao: 33.0, flecha: 0.5, angulo: 0.0 },
        2: { tipo_rede: 'Convencional', tipo_cabo: '397MCM-CA, Nu', vao: 33.0, flecha: 0.5, angulo: 30.0 },
        3: { tipo_rede: 'Convencional', tipo_cabo: '397MCM-CA, Nu', vao: 33.0, flecha: 0.5, angulo: -30.0 },
        4: { tipo_rede: 'Convencional', tipo_cabo: '397MCM-CA, Nu', vao: 33.0, flecha: 0.5, angulo: 45.0 },
      })
    )
    .withNivelMT2(buildTravessias())
    .withNivelBT(buildTravessias())
    .withNivelBTZ(buildTravessias())
    .withNivelRAL(buildTravessias())
    .withResultado(
      buildResultado({
        mt1_tracao: 450.5,
        mt1_angulo: 12.3,
        total_tracao: 450.5,
        total_angulo: 12.3,
        poste_ecc: 120.0,
        texto_mt1: 'MT1: 450.5 daN @ 12.3°',
        texto_total: 'Total final: 450.5 daN @ 12.3°',
      })
    )
    .build();
}

function buildBatchPayload(runId) {
  return {
    projeto_dados: buildProjetoPayload(runId, true),
    ponto_dados: buildPontoPayload(runId, 'B'),
    niveis: criarCalculoPayload()
      .forPonto(0)
      .withNivelMT1(
        buildTravessias({
          1: { tipo_rede: 'Convencional', tipo_cabo: '397MCM', vao: 40, flecha: 0.6 },
          2: { tipo_rede: 'Convencional', tipo_cabo: '397MCM', vao: 40, flecha: 0.6 },
          3: { tipo_rede: 'Convencional', tipo_cabo: '397MCM', vao: 40, flecha: 0.6 },
          4: { tipo_rede: 'Convencional', tipo_cabo: '397MCM', vao: 40, flecha: 0.6 },
        })
      )
      .withNivelMT2(buildTravessias())
      .withNivelBT(buildTravessias())
      .withNivelBTZ(buildTravessias())
      .withNivelRAL(buildTravessias())
      .build()
      .niveis,
    resultado: buildResultado({
      mt1_tracao: 480.0,
      mt1_angulo: 15.0,
      total_tracao: 480.0,
      total_angulo: 15.0,
      poste_ecc: 130.0,
      texto_mt1: 'MT1: 480.0 daN @ 15.0°',
      texto_total: 'Total: 480.0 daN @ 15.0°',
    }),
  };
}

async function apiPost(request, path, data) {
  return request.post(`${API_BASE_URL}${path}`, { headers: buildHeaders(), data });
}

async function apiGet(request, path) {
  return request.get(`${API_BASE_URL}${path}`, { headers: buildHeaders() });
}

function expectSnapshotSemantics(snapshot, expectedPontoId, expectedTotalTracao, expectedTotalAngulo) {
  expect(snapshot).toHaveProperty('ponto_id', expectedPontoId);
  expect(Array.isArray(snapshot.niveis)).toBe(true);
  expect(snapshot.niveis).toHaveLength(5);
  expect(snapshot.niveis.map((nivel) => nivel.nivel)).toEqual(LEVELS);

  snapshot.niveis.forEach((nivel) => {
    expect(Array.isArray(nivel.travessias)).toBe(true);
    expect(nivel.travessias).toHaveLength(4);
    expect(nivel.travessias.map((travessia) => travessia.posicao)).toEqual([1, 2, 3, 4]);
  });

  expect(snapshot.resultado.total_tracao).toBe(expectedTotalTracao);
  expect(snapshot.resultado.total_angulo).toBe(expectedTotalAngulo);

  const numeros = String(snapshot.resultado.texto_total).replace(',', '.').match(/-?\d+(?:\.\d+)?/g) || [];
  expect(numeros.length).toBeGreaterThanOrEqual(2);
  expect(Number(numeros[0])).toBeCloseTo(snapshot.resultado.total_tracao, 1);
  expect(Number(numeros[1])).toBeCloseTo(snapshot.resultado.total_angulo, 1);
}

test.describe.serial('Complete Hierarchy Persistence Flow', () => {
  const RUN_ID = `${Date.now()}`.slice(-6);
  let projetoId;
  let pontoId;

  test('POST /projetos — creates new projeto with metadata', async ({ request }) => {
    const projetoPayload = buildProjetoPayload(RUN_ID);
    const response = await apiPost(request, '/projetos', projetoPayload);

    expect(response.status()).toBe(201);
    const data = await response.json();
    expect(data).toHaveProperty('id');
    expect(data).toHaveProperty('nome', projetoPayload.nome);
    projetoId = data.id;
  });

  test('POST /projetos/{projeto_id}/pontos — creates ponto', async ({ request }) => {
    const pontoPayload = buildPontoPayload(RUN_ID, 'P');
    const response = await apiPost(request, `/projetos/${projetoId}/pontos`, pontoPayload);

    expect(response.status()).toBe(201);
    const data = await response.json();
    expect(data).toHaveProperty('id');
    expect(data).toHaveProperty('ponto', pontoPayload.ponto);
    pontoId = data.id;
  });

  test('GET /pontos/{ponto_id}/snapshot — returns 403 for different identity', async ({ playwright }) => {
    const isolatedRequest = await playwright.request.newContext();
    try {
      const response = await isolatedRequest.get(`${API_BASE_URL}/pontos/${pontoId}/snapshot`, {
        headers: buildHeaders(),
      });
      expect(response.status()).toBe(403);
    } finally {
      await isolatedRequest.dispose();
    }
  });

  test('GET /pontos/{ponto_id}/snapshot — returns 404 when snapshot is absent', async ({ request }) => {
    const noSnapshotPoint = await apiPost(request, `/projetos/${projetoId}/pontos`, buildPontoPayload(`${RUN_ID}9`, 'N'));
    expect(noSnapshotPoint.status()).toBe(201);
    const noSnapshotData = await noSnapshotPoint.json();

    const snapshotResponse = await apiGet(request, `/pontos/${noSnapshotData.id}/snapshot`);
    expect(snapshotResponse.status()).toBe(404);
  });

  test('POST /pontos/{ponto_id}/calculo — returns 422 when ponto_id diverges from URL', async ({ request }) => {
    const payload = buildSnapshotPayload(pontoId);
    const response = await apiPost(request, `/pontos/${pontoId}/calculo`, {
      ...payload,
      ponto_id: pontoId + 1,
    });
    expect(response.status()).toBe(422);
  });

  test('POST /pontos/{ponto_id}/calculo — saves niveis + travessias + resultado', async ({ request }) => {
    const response = await apiPost(request, `/pontos/${pontoId}/calculo`, buildSnapshotPayload(pontoId));
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty('saved', true);
    expect(data).toHaveProperty('ponto_id', pontoId);
  });

  test('GET /pontos/{ponto_id}/snapshot — verifies semantic hierarchy and totals', async ({ request }) => {
    const response = await apiGet(request, `/pontos/${pontoId}/snapshot`);
    expect(response.status()).toBe(200);
    const snapshot = await response.json();

    expectSnapshotSemantics(snapshot, pontoId, 450.5, 12.3);
    expect(snapshot.niveis[0].travessias[1]).toMatchObject({ posicao: 2, tipo_cabo: '397MCM-CA, Nu', angulo: 30.0 });
  });
});

test.describe.serial('Batch Persistence Flow', () => {
  const RUN_ID = `${Date.now()}`.slice(-6);

  test('POST /projetos/batch-save — atomic insert projeto + ponto + calculo', async ({ request }) => {
    const response = await apiPost(request, '/projetos/batch-save', buildBatchPayload(RUN_ID));
    expect(response.status()).toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('projeto_id');
    expect(data).toHaveProperty('ponto_id');

    const snapshotResponse = await apiGet(request, `/pontos/${data.ponto_id}/snapshot`);
    expect(snapshotResponse.status()).toBe(200);
    const snapshot = await snapshotResponse.json();
    expectSnapshotSemantics(snapshot, data.ponto_id, 480.0, 15.0);
  });
});
