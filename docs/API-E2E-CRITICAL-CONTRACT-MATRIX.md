# Matriz de Contrato Critico API-E2E

Data de referencia: 2026-03-24.

Escopo: fluxo critico `Projeto -> Ponto -> Persistido -> Snapshot`.

Objetivo: definir oficialmente contratos de sucesso e erro com semantica unica
para `200`, `401`, `403`, `404`, `422` e alinhar cobertura entre API e E2E.

## 1. Regras de semantica HTTP

- `200 OK`: operacao concluida com sucesso e payload valido de retorno.
- `401 Unauthorized`: identidade de mutacao ausente/invalida quando JWT e obrigatorio.
- `403 Forbidden`: identidade autenticada sem permissao para o recurso.
- `404 Not Found`: recurso de dominio inexistente ou snapshot ainda ausente.
- `422 Unprocessable Entity`: payload valido em formato, mas invalido para regra de contrato/dominio.

## 2. Matriz oficial por endpoint critico

## 2.1 POST /api/projetos

Sucesso:

- `201` projeto criado.

Erros oficiais:

- `401` sem JWT quando `AUTH_REQUIRE_JWT_FOR_MUTATIONS=true`.
- `422` erro de validacao de payload (schema).

Exemplo payload (abreviado):

```json
{
  "orgao": "TEST_ORGAO",
  "ns": "NS-001",
  "nome": "Projeto Teste",
  "endereco": "Rua Teste, 123",
  "estudado_por": "E2E Bot",
  "matricula": "9999",
  "data_estudo": "2026-03-24"
}
```

Exemplo resposta sucesso:

```json
{
  "id": "11111111-1111-1111-1111-111111111111",
  "orgao": "TEST_ORGAO",
  "nome": "Projeto Teste"
}
```

## 2.2 POST /api/projetos/{projeto_id}/pontos

Sucesso:

- `201` ponto criado no projeto.

Erros oficiais:

- `401` sem JWT quando exigido por configuracao.
- `403` usuario autenticado sem permissao no projeto.
- `404` projeto inexistente.
- `422` payload invalido.

Exemplo payload:

```json
{
  "ponto": "P001",
  "tipo_poste": "DT",
  "modelo_poste": "11/600"
}
```

Exemplo resposta sucesso:

```json
{
  "id": "22222222-2222-2222-2222-222222222222",
  "projeto_id": "11111111-1111-1111-1111-111111111111",
  "ponto": "P001",
  "tipo_poste": "DT",
  "modelo_poste": "11/600"
}
```

## 2.3 POST /api/pontos/{ponto_id}/calculo

Sucesso:

- `200` snapshot persistido.

Erros oficiais:

- `401` sem JWT quando exigido por configuracao.
- `403` usuario autenticado sem permissao no ponto.
- `404` ponto inexistente.
- `422` `ponto_id` do payload diferente da rota ou payload invalido.

Exemplo payload:

```json
{
  "ponto_id": "22222222-2222-2222-2222-222222222222",
  "niveis": [
    {
      "nivel": "MT1",
      "altura_poste": 11,
      "altura_ancoragem": 9.2,
      "travessias": [
        {
          "posicao": 1,
          "tipo_rede": "",
          "tipo_cabo": "",
          "vao": 0,
          "flecha": 0,
          "angulo": 0,
          "qtd_ligacoes": 0,
          "qtd_cabos": 0
        }
      ]
    }
  ],
  "resultado": {
    "mt1_tracao": 450.5,
    "mt1_angulo": 12.3,
    "mt2_tracao": 0,
    "mt2_angulo": 0,
    "bt_tracao": 0,
    "bt_angulo": 0,
    "btz_tracao": 0,
    "btz_angulo": 0,
    "ral_tracao": 0,
    "ral_angulo": 0,
    "total_tracao": 450.5,
    "total_angulo": 12.3,
    "poste_ecc": 120,
    "texto_mt1": "MT1: 450.5 daN @ 12.3°",
    "texto_mt2": "",
    "texto_bt": "",
    "texto_btz": "",
    "texto_ral": "",
    "texto_total": "Total final: 450.5 daN @ 12.3°"
  }
}
```

Exemplo resposta sucesso (abreviado):

```json
{
  "saved": true,
  "ponto_id": "22222222-2222-2222-2222-222222222222"
}
```

## 2.4 GET /api/pontos/{ponto_id}/snapshot

Sucesso:

- `200` snapshot completo retornado.

Erros oficiais:

- `401` sem JWT quando exigido por configuracao.
- `403` usuario autenticado sem permissao no ponto.
- `404` ponto inexistente ou snapshot ainda nao disponivel para o ponto.

Exemplo resposta sucesso:

```json
{
  "ponto_id": "22222222-2222-2222-2222-222222222222",
  "niveis": [
    {
      "id": "33333333-3333-3333-3333-333333333333",
      "nivel": "MT1",
      "altura_poste": 11,
      "altura_ancoragem": 9.2,
      "travessias": [
        {
          "posicao": 1,
          "tipo_rede": "Convencional",
          "tipo_cabo": "397MCM-CA, Nu",
          "vao": 33,
          "flecha": 0.5,
          "angulo": 0,
          "qtd_ligacoes": 0,
          "qtd_cabos": 0
        }
      ]
    }
  ],
  "resultado": {
    "total_tracao": 450.5,
    "total_angulo": 12.3,
    "texto_total": "Total final: 450.5 daN @ 12.3°"
  }
}
```

## 3. Evidencia automatizada da matriz

Cobertura API (backend):

- `python/tests/test_api_e2e_contract_matrix.py`
- valida `200`, `401`, `403`, `404`, `422` com dependencia controlada.

Cobertura E2E (fluxo real):

- `e2e/test_complete_hierarchy_flow.spec.js`
- valida `200` (persistencia/snapshot), `404` (snapshot ausente), `422` (ponto_id divergente), e `403` por identidade distinta.

## 4. Regra de gate

Gate do fluxo critico so deve passar quando:

1. Contrato HTTP desta matriz estiver sem regressao.
2. E2E de hierarquia/snapshot estiver verde.
3. Nao houver divergencia semantica entre API e E2E no ciclo atual.
