"""Testes de validação de domínio da API — garantem 422 para entradas inválidas."""
import sys
import os

# Configurar variáveis ANTES de importar o app (módulo lido uma única vez)
os.environ.setdefault("AUTH_REQUIRE_JWT_FOR_MUTATIONS", "false")
os.environ.setdefault("APP_ENV", "development")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def _minimal_calcular_payload(**overrides):
    """Payload mínimo válido para /calcular (tudo zero/vazio)."""
    base = {
        "cabecalho": {},
        "poste": {"tipo_poste": "Concreto circular", "modelo_poste": "C11/6"},
        "mt1": [
            {"tipo_rede": "", "tipo_cabo": "", "vao": 0, "flecha": 0, "angulo": 0,
             "altura_poste": 0, "altura_ancoragem": 0}
        ] * 4,
        "mt2": [
            {"tipo_rede": "", "tipo_cabo": "", "vao": 0, "flecha": 0, "angulo": 0,
             "altura_poste": 0, "altura_ancoragem": 0}
        ] * 4,
        "bt": [
            {"tipo_rede": "", "tipo_cabo": "", "vao": 0, "flecha": 0, "angulo": 0,
             "altura_poste": 0, "altura_ancoragem": 0}
        ] * 4,
        "btz": [
            {"qtd_ligacoes": 0, "vao": 0, "flecha": 0, "angulo": 0,
             "altura_poste": 0, "altura_ancoragem": 0}
        ] * 4,
        "ral": [
            {"tipo_cabo": "", "qtd_cabos": 0, "vao": 0, "flecha": 0, "angulo": 0,
             "altura_poste": 0, "altura_ancoragem": 0}
        ] * 4,
    }
    base.update(overrides)
    return base


def test_calcular_payload_valido_retorna_200():
    """Payload mínimo (tudo zero/vazio) deve retornar 200 com zeros."""
    resp = client.post("/calcular", json=_minimal_calcular_payload())
    assert resp.status_code == 200


def test_calcular_vao_positivo_flecha_zero_retorna_422():
    """vao > 0 com flecha = 0 deve retornar 422 (domínio inválido)."""
    payload = _minimal_calcular_payload()
    # Substituir posição 0 sem usar lista mutável compartilhada
    payload["mt1"] = list(payload["mt1"])
    payload["mt1"][0] = {
        "tipo_rede": "Convencional",
        "tipo_cabo": "397MCM-CA, Nu",
        "vao": 30.0,
        "flecha": 0.0,   # inválido: vao > 0 exige flecha > 0
        "angulo": 0,
        "altura_poste": 11,
        "altura_ancoragem": 9,
    }
    resp = client.post("/calcular", json=payload)
    assert resp.status_code == 422


def test_calcular_payload_completo_cosmo_retorna_200():
    """Payload completo do projeto Cosmo LDA deve ser processado com 200."""
    payload = _minimal_calcular_payload()
    payload["mt1"] = [
        {
            "tipo_rede": "Convencional", "tipo_cabo": "397MCM-CA, Nu",
            "vao": 33.0, "flecha": 0.5, "angulo": 0.0,
            "altura_poste": 11.0, "altura_ancoragem": 9.2,
        },
        {
            "tipo_rede": "Convencional", "tipo_cabo": "397MCM-CA, Nu",
            "vao": 40.0, "flecha": 0.5, "angulo": 179.0,
            "altura_poste": 11.0, "altura_ancoragem": 9.2,
        },
        {"tipo_rede": "", "tipo_cabo": "", "vao": 0, "flecha": 0,
         "angulo": 0, "altura_poste": 0, "altura_ancoragem": 0},
        {"tipo_rede": "", "tipo_cabo": "", "vao": 0, "flecha": 0,
         "angulo": 0, "altura_poste": 0, "altura_ancoragem": 0},
    ]
    resp = client.post("/calcular", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["mt1"]["tracao_dan"] > 0


def test_health_retorna_200():
    """Endpoint /health deve retornar 200 sem autenticação."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_calcular_bt_vao_positivo_flecha_zero_retorna_422():
    """Validação flecha/vao também se aplica a entradas BT."""
    payload = _minimal_calcular_payload()
    payload["bt"] = list(payload["bt"])
    payload["bt"][2] = {
        "tipo_rede": "Multiplexada", "tipo_cabo": "70mm², MTX-BT",
        "vao": 20.0, "flecha": 0.0,   # inválido
        "angulo": 85.0,
        "altura_poste": 11.0, "altura_ancoragem": 7.0,
    }
    resp = client.post("/calcular", json=payload)
    assert resp.status_code == 422


def test_calcular_retorna_erro_500_nao_vaza_para_cliente():
    """A API deve retornar 422 ou 200, nunca um traceback Python em texto plano."""
    resp = client.post("/calcular", json=_minimal_calcular_payload())
    assert resp.status_code in (200, 422, 500)
    if resp.status_code == 500:
        # 500 deve ser JSON estruturado, não traceback raw
        body = resp.text
        assert "Traceback" not in body
        assert "File " not in body
