import { test, expect } from '@playwright/test';
import { criarProjeto, criarPonto, criarTravessia, criarResultado, criarCalculoPayload } from './helpers/test_factories.js';
import crypto from 'node:crypto';

const API_BASE_URL = process.env.API_URL || 'http://127.0.0.1:8000/api';
const LEVELS = ['MT1', 'MT2', 'BT', 'BTZ', 'RAL'];
const AUTH_JWT_SECRET = process.env.AUTH_JWT_SECRET || 'release-smoke-default-secret';
const JWT_USER_ID = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';

function base64url(input) {
  return Buffer.from(input)
    .toString('base64')
    .replace(/=/g, '')
    .replace(/\+/g, '-')
    .replace(/\//g, '_');
}

function createSmokeJwt() {
  const now = Math.floor(Date.now() / 1000);
  const header = { alg: 'HS256', typ: 'JWT' };
  const payload = {
    sub: JWT_USER_ID,
    role: 'user',
    iat: now,
    exp: now + 3600,
  };
  const encodedHeader = base64url(JSON.stringify(header));
  const encodedPayload = base64url(JSON.stringify(payload));
  const signature = crypto
    .createHmac('sha256', AUTH_JWT_SECRET)
    .update(`${encodedHeader}.${encodedPayload}`)
    .digest('base64')
    .replace(/=/g, '')
    .replace(/\+/g, '-')
    .replace(/\//g, '_');
  return `${encodedHeader}.${encodedPayload}.${signature}`;
}

const WRITE_JWT = createSmokeJwt();

function buildHeaders() {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${WRITE_JWT}`,
  };
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

function buildProjetoPayload(runId) {
  return criarProjeto()
    .withOrgao('SMOKE_ORGAO')
    .withNs(`SMOKE-${runId}`)
    .withNome(`SmokeProjeto${runId}`)
    .withEndereco('Rua Smoke, 123')
    .withEstudadoPor('Smoke Bot')
    .withMatricula('7001')
    .withDataEstudo(new Date().toLocaleDateString('pt-BR'))
    .build();
}

function buildPontoPayload(runId) {
  return criarPonto()
    .withRunId(runId, 'S')
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

async function apiPost(request, path, data) {
  return request.post(`${API_BASE_URL}${path}`, { headers: buildHeaders(), data });
}

async function apiGet(request, path) {
  return request.get(`${API_BASE_URL}${path}`, { headers: buildHeaders() });
}

test.describe.serial('Release Smoke - Contract/Auth/Snapshot', () => {
  const runId = `${Date.now()}`.slice(-8);
  let projetoId;
  let pontoId;

  test('auth gate: mutacao sem JWT retorna 401', async ({ request }) => {
    const response = await request.post(`${API_BASE_URL}/projetos`, {
      headers: { 'Content-Type': 'application/json' },
      data: buildProjetoPayload(`${runId}0`),
    });
    expect(response.status()).toBe(401);
  });

  test('cria projeto e ponto base para smoke', async ({ request }) => {
    const projetoResp = await apiPost(request, '/projetos', buildProjetoPayload(runId));
    expect(projetoResp.status()).toBe(201);
    expect(projetoResp.headers()['x-operation-id']).toBeTruthy();
    projetoId = (await projetoResp.json()).id;

    const pontoResp = await apiPost(request, `/projetos/${projetoId}/pontos`, buildPontoPayload(runId));
    expect(pontoResp.status()).toBe(201);
    expect(pontoResp.headers()['x-operation-id']).toBeTruthy();
    pontoId = (await pontoResp.json()).id;
  });

  test('contrato de erro: snapshot ausente retorna 404', async ({ request }) => {
    const outroPontoResp = await apiPost(request, `/projetos/${projetoId}/pontos`, buildPontoPayload(`${runId}9`));
    expect(outroPontoResp.status()).toBe(201);
    expect(outroPontoResp.headers()['x-operation-id']).toBeTruthy();
    const outroPontoId = (await outroPontoResp.json()).id;

    const snapshotResp = await apiGet(request, `/pontos/${outroPontoId}/snapshot`);
    expect(snapshotResp.status()).toBe(404);
    expect(snapshotResp.headers()['x-operation-id']).toBeTruthy();
  });

  test('contrato de erro: ponto_id divergente retorna 422', async ({ request }) => {
    const payload = buildSnapshotPayload(pontoId);
    const resp = await apiPost(request, `/pontos/${pontoId}/calculo`, {
      ...payload,
      ponto_id: `${pontoId}-mismatch`,
    });
    expect(resp.status()).toBe(422);
    expect(resp.headers()['x-operation-id']).toBeTruthy();
  });

  test('snapshot persistido retorna 200 com semantica minima', async ({ request }) => {
    const saveResp = await apiPost(request, `/pontos/${pontoId}/calculo`, buildSnapshotPayload(pontoId));
    expect(saveResp.status()).toBe(200);
    expect(saveResp.headers()['x-operation-id']).toBeTruthy();

    const snapshotResp = await apiGet(request, `/pontos/${pontoId}/snapshot`);
    expect(snapshotResp.status()).toBe(200);
    expect(snapshotResp.headers()['x-operation-id']).toBeTruthy();
    const snapshot = await snapshotResp.json();

    expect(snapshot).toHaveProperty('ponto_id', pontoId);
    expect(Array.isArray(snapshot.niveis)).toBe(true);
    expect(snapshot.niveis.map((nivel) => nivel.nivel)).toEqual(LEVELS);
    expect(snapshot.resultado.total_tracao).toBe(450.5);
    expect(snapshot.resultado.total_angulo).toBe(12.3);
  });

  // SLO: snapshot must be retrievable within 100 ms of a confirmed save.
  // If absent (404), the undue-absence counter is incremented so the
  // /monitoring/snapshot/slos endpoint reflects the real absence rate.
  test('slo: snapshot recuperavel imediatamente apos save (ausencia indevida)', async ({ request }) => {
    const absencePontoResp = await apiPost(
      request,
      `/projetos/${projetoId}/pontos`,
      buildPontoPayload(`${runId}A`),
    );
    expect(absencePontoResp.status()).toBe(201);
    const absencePontoId = (await absencePontoResp.json()).id;

    // Save snapshot
    const saveResp = await apiPost(
      request,
      `/pontos/${absencePontoId}/calculo`,
      buildSnapshotPayload(absencePontoId),
    );
    expect(saveResp.status()).toBe(200);
    expect(saveResp.headers()['x-operation-id']).toBeTruthy();

    // Immediate retrieve – should be 200, not 404
    const retrieveResp = await apiGet(request, `/pontos/${absencePontoId}/snapshot`);
    expect(retrieveResp.headers()['x-operation-id']).toBeTruthy();

    if (retrieveResp.status() === 404) {
      // Report undue absence to the metrics system so the SLO gauge is updated
      await request.post(`${API_BASE_URL}/monitoring/snapshot/record-undue-absence`, {
        headers: buildHeaders(),
      });
    }

    // Hard assertion: persistence must be immediately consistent
    expect(retrieveResp.status()).toBe(200);
  });
});
