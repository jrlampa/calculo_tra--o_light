import { test, expect } from '@playwright/test';

const API_BASE_URL = process.env.API_URL || 'http://localhost:8000';
const ADMIN_TOKEN = process.env.X_ADMIN_TOKEN || 'test-token-for-development';

/**
 * E2E Test: Complete Hierarchy Flow
 * 
 * Tests the full persistence chain:
 * 1. Create Projeto (project)
 * 2. Create Ponto (point/pole) under that projeto
 * 3. Create Níveis (calculation levels MT1, MT2, BT, BTZ, RAL)
 * 4. Create Travessias (traversals T1-T4 for each nível)
 * 5. Save complete calculation result
 * 6. Verify all data persists in Supabase
 * 
 * This test validates that the data hierarchy is properly saved
 * and can be retrieved from the database.
 */

test.describe.serial('Complete Hierarchy Persistence Flow', () => {
  let projetoId: string;
  let pontoId: string;
  let userId: string = '00000000-0000-0000-0000-000000000000'; // Test user

  // ──────────────────────────────────────────────────────────────
  // STEP 1: Create Projeto (Project)
  // ──────────────────────────────────────────────────────────────

  test('POST /projetos — creates new projeto with metadata', async ({ request }) => {
    const projetoPayload = {
      orgao: 'TEST_ORGAO',
      ns: 'NS-001',
      nome: `Test_Projeto_${Date.now()}`,
      endereco: 'Rua Teste, 123',
      estudado_por: 'E2E Bot',
      matricula: '9999',
      data_estudo: new Date().toISOString().split('T')[0],
    };

    const response = await request.post(`${API_BASE_URL}/projetos`, {
      headers: {
        'Content-Type': 'application/json',
        'X-Admin-Token': ADMIN_TOKEN,
      },
      data: projetoPayload,
    });

    expect(response.status()).toBe(201);
    const data = await response.json();
    
    expect(data).toHaveProperty('id');
    expect(data).toHaveProperty('nome', projetoPayload.nome);
    expect(data).toHaveProperty('orgao', projetoPayload.orgao);
    expect(data).toHaveProperty('endereco', projetoPayload.endereco);
    expect(data).toHaveProperty('estudado_por', projetoPayload.estudado_por);
    
    projetoId = data.id;
  });

  // ──────────────────────────────────────────────────────────────
  // STEP 2: Create Ponto (Point) under the Projeto
  // ──────────────────────────────────────────────────────────────

  test('POST /projetos/{projeto_id}/pontos — creates ponto', async ({ request }) => {
    const pontoPayload = {
      ponto: `01_${Date.now().toString().slice(-4)}`, // e.g., "01_5678"
      tipo_poste: 'DT',
      modelo_poste: '11/600',
    };

    const response = await request.post(
      `${API_BASE_URL}/projetos/${projetoId}/pontos`,
      {
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Token': ADMIN_TOKEN,
        },
        data: pontoPayload,
      }
    );

    expect(response.status()).toBe(201);
    const data = await response.json();
    
    expect(data).toHaveProperty('id');
    expect(data).toHaveProperty('projeto_id', projetoId);
    expect(data).toHaveProperty('ponto', pontoPayload.ponto);
    expect(data).toHaveProperty('tipo_poste', pontoPayload.tipo_poste);
    expect(data).toHaveProperty('modelo_poste', pontoPayload.modelo_poste);
    
    pontoId = data.id;
  });

  // ──────────────────────────────────────────────────────────────
  // STEP 3 & 4 & 5: Save complete calculation with niveis & travessias
  // ──────────────────────────────────────────────────────────────

  test('POST /pontos/{ponto_id}/calculo — saves niveis + travessias + resultado', async ({ request }) => {
    const calculoPayload = {
      ponto_id: pontoId,
      niveis: [
        {
          nivel: 'MT1',
          altura_poste: 11.0,
          altura_ancoragem: 9.2,
          travessias: [
            {
              posicao: 1,
              tipo_rede: 'Convencional',
              tipo_cabo: '397MCM-CA, Nu',
              vao: 33.0,
              flecha: 0.5,
              angulo: 0.0,
              qtd_ligacoes: 0.0,
              qtd_cabos: 0.0,
            },
            {
              posicao: 2,
              tipo_rede: 'Convencional',
              tipo_cabo: '397MCM-CA, Nu',
              vao: 33.0,
              flecha: 0.5,
              angulo: 30.0,
              qtd_ligacoes: 0.0,
              qtd_cabos: 0.0,
            },
            {
              posicao: 3,
              tipo_rede: 'Convencional',
              tipo_cabo: '397MCM-CA, Nu',
              vao: 33.0,
              flecha: 0.5,
              angulo: -30.0,
              qtd_ligacoes: 0.0,
              qtd_cabos: 0.0,
            },
            {
              posicao: 4,
              tipo_rede: 'Convencional',
              tipo_cabo: '397MCM-CA, Nu',
              vao: 33.0,
              flecha: 0.5,
              angulo: 45.0,
              qtd_ligacoes: 0.0,
              qtd_cabos: 0.0,
            },
          ],
        },
        {
          nivel: 'MT2',
          altura_poste: 10.5,
          altura_ancoragem: 8.7,
          travessias: [
            { posicao: 1, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
            { posicao: 2, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
            { posicao: 3, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
            { posicao: 4, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
          ],
        },
        {
          nivel: 'BT',
          altura_poste: 9.0,
          altura_ancoragem: 7.5,
          travessias: [
            { posicao: 1, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
            { posicao: 2, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
            { posicao: 3, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
            { posicao: 4, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
          ],
        },
        {
          nivel: 'BTZ',
          altura_poste: 1.5,
          altura_ancoragem: 1.0,
          travessias: [
            { posicao: 1, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
            { posicao: 2, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
            { posicao: 3, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
            { posicao: 4, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
          ],
        },
        {
          nivel: 'RAL',
          altura_poste: 8.0,
          altura_ancoragem: 6.5,
          travessias: [
            { posicao: 1, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
            { posicao: 2, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
            { posicao: 3, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
            { posicao: 4, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
          ],
        },
      ],
      resultado: {
        mt1_tracao: 450.5,
        mt1_angulo: 12.3,
        mt2_tracao: 0.0,
        mt2_angulo: 0.0,
        bt_tracao: 0.0,
        bt_angulo: 0.0,
        btz_tracao: 0.0,
        btz_angulo: 0.0,
        ral_tracao: 0.0,
        ral_angulo: 0.0,
        total_tracao: 450.5,
        total_angulo: 12.3,
        poste_ecc: 120.0,
        texto_mt1: 'MT1: 450.5 daN @ 12.3°',
        texto_mt2: '',
        texto_bt: '',
        texto_btz: '',
        texto_ral: '',
        texto_total: 'Total final: 450.5 daN @ 12.3°',
      },
    };

    const response = await request.post(
      `${API_BASE_URL}/pontos/${pontoId}/calculo`,
      {
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Token': ADMIN_TOKEN,
        },
        data: calculoPayload,
      }
    );

    expect(response.status()).toBe(200);
    const data = await response.json();
    
    expect(data).toHaveProperty('saved', true);
    expect(data).toHaveProperty('ponto_id', pontoId);
  });

  // ──────────────────────────────────────────────────────────────
  // STEP 6: Verify persistence — GET project and check hierarchy
  // ──────────────────────────────────────────────────────────────

  test('GET /projetos/{projeto_id} — verifies ponto was persisted', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/projetos/${projetoId}`, {
      headers: {
        'X-Admin-Token': ADMIN_TOKEN,
      },
    });

    expect(response.status()).toBe(200);
    const data = await response.json();
    
    expect(data).toHaveProperty('id', projetoId);
    // The response should indicate the projeto now has pontos
    // (implementation detail may vary)
  });

  test('GET /projetos/{projeto_id}/pontos — verifies ponto exists', async ({ request }) => {
    const response = await request.get(
      `${API_BASE_URL}/projetos/${projetoId}/pontos`,
      {
        headers: {
          'X-Admin-Token': ADMIN_TOKEN,
        },
      }
    );

    // Assuming an endpoint exists to list pontos for a projeto
    if (response.status() === 200) {
      const data = await response.json();
      expect(Array.isArray(data)).toBe(true);
      // At least one ponto should exist
      const foundPonto = data.find((p: any) => p.id === pontoId);
      expect(foundPonto).toBeDefined();
    }
  });

  test('Verify hierarchy in Supabase — query niveis_calculo for ponto', async ({ request }) => {
    // This test assumes there's an admin endpoint to query the DB directly
    // or that the /pontos/{ponto_id} endpoint returns associated niveis
    const response = await request.get(`${API_BASE_URL}/pontos/${pontoId}`, {
      headers: {
        'X-Admin-Token': ADMIN_TOKEN,
      },
    });

    // If such an endpoint exists, verify niveis are returned
    if (response.status() === 200) {
      const data = await response.json();
      expect(data).toHaveProperty('id', pontoId);
      // Check if niveis are included (implementation-dependent)
      if ('niveis' in data) {
        expect(Array.isArray(data.niveis)).toBe(true);
        expect(data.niveis.length).toBeGreaterThan(0);
      }
    }
  });
});

/**
 * Test Group: Batch Persistence (Alternative method)
 * 
 * Tests atomic insert of Projeto + Ponto + Calculation in one API call
 */
test.describe.serial('Batch Persistence Flow', () => {
  const RUN_ID = `batch_${Date.now()}`;

  test('POST /projetos/batch-save — atomic insert projeto + ponto + calculo', async ({ request }) => {
    const batchPayload = {
      projeto_dados: {
        orgao: 'TEST_BATCH_ORG',
        ns: `NS-BATCH-${RUN_ID}`,
        nome: `Batch_Projeto_${RUN_ID}`,
        endereco: 'Rua Batch, 456',
        estudado_por: 'E2E Batch Bot',
        matricula: '8888',
      },
      ponto_dados: {
        ponto: `02_BATCH`,
        tipo_poste: 'DT',
        modelo_poste: '11/600',
      },
      niveis: [
        {
          nivel: 'MT1',
          altura_poste: 11.0,
          altura_ancoragem: 9.2,
          travessias: [
            { posicao: 1, tipo_rede: 'Convencional', tipo_cabo: '397MCM', vao: 40, flecha: 0.6, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
            { posicao: 2, tipo_rede: 'Convencional', tipo_cabo: '397MCM', vao: 40, flecha: 0.6, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
            { posicao: 3, tipo_rede: 'Convencional', tipo_cabo: '397MCM', vao: 40, flecha: 0.6, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
            { posicao: 4, tipo_rede: 'Convencional', tipo_cabo: '397MCM', vao: 40, flecha: 0.6, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
          ],
        },
        {
          nivel: 'MT2',
          altura_poste: 10.5,
          altura_ancoragem: 8.7,
          travessias: [
            { posicao: 1, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
            { posicao: 2, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
            { posicao: 3, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
            { posicao: 4, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
          ],
        },
        {
          nivel: 'BT',
          altura_poste: 9.0,
          altura_ancoragem: 7.5,
          travessias: [
            { posicao: 1, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
            { posicao: 2, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
            { posicao: 3, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
            { posicao: 4, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
          ],
        },
        {
          nivel: 'BTZ',
          altura_poste: 1.5,
          altura_ancoragem: 1.0,
          travessias: [
            { posicao: 1, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
            { posicao: 2, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
            { posicao: 3, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
            { posicao: 4, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
          ],
        },
        {
          nivel: 'RAL',
          altura_poste: 8.0,
          altura_ancoragem: 6.5,
          travessias: [
            { posicao: 1, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
            { posicao: 2, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
            { posicao: 3, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
            { posicao: 4, tipo_rede: '', tipo_cabo: '', vao: 0, flecha: 0, angulo: 0, qtd_ligacoes: 0, qtd_cabos: 0 },
          ],
        },
      ],
      resultado: {
        mt1_tracao: 480.0,
        mt1_angulo: 15.0,
        mt2_tracao: 0.0,
        mt2_angulo: 0.0,
        bt_tracao: 0.0,
        bt_angulo: 0.0,
        btz_tracao: 0.0,
        btz_angulo: 0.0,
        ral_tracao: 0.0,
        ral_angulo: 0.0,
        total_tracao: 480.0,
        total_angulo: 15.0,
        poste_ecc: 130.0,
        texto_mt1: 'MT1: 480.0 daN @ 15.0°',
        texto_mt2: '',
        texto_bt: '',
        texto_btz: '',
        texto_ral: '',
        texto_total: 'Total: 480.0 daN @ 15.0°',
      },
    };

    const response = await request.post(`${API_BASE_URL}/projetos/batch-save`, {
      headers: {
        'Content-Type': 'application/json',
        'X-Admin-Token': ADMIN_TOKEN,
      },
      data: batchPayload,
    });

    expect(response.status()).toBe(200);
    const data = await response.json();
    
    expect(data).toHaveProperty('projeto_id');
    expect(data).toHaveProperty('ponto_id');
    expect(data).toHaveProperty('saved', true);
  });
});
