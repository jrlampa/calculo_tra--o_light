"""Contract tests for critical Projeto -> Ponto -> Persistido -> Snapshot flow."""

from __future__ import annotations

import os
import sys
from typing import Any

import pytest
from fastapi.testclient import TestClient

# Ensure local imports resolve before importing app.
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from api.auth import CurrentUser
from api.main import app
from api.routers import projetos as projetos_router
import api.main as api_main


PROJETO_ID = "11111111-1111-1111-1111-111111111111"
PONTO_ID = "22222222-2222-2222-2222-222222222222"
USER_A_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


class _MockConn:
    """Mock DB connection that passes fetchval health-check."""

    async def fetchval(self, query: str) -> int:
        return 1


class _MockPool:
    """Mock connection pool supporting `async with pool.acquire() as conn`."""

    def acquire(self):
        return self

    async def __aenter__(self):
        return _MockConn()

    async def __aexit__(self, *args: Any) -> None:
        pass


class SupabaseStub:
    def __init__(self) -> None:
        self.is_enabled = True
        self.projeto_exists_value = True
        self.ponto_exists_value = True
        self.can_access_projeto_value = True
        self.can_access_ponto_value = True
        self.save_snapshot_value = True
        self.snapshot_payload: dict[str, Any] | None = None

    async def _get_pool(self) -> _MockPool:
        return _MockPool()

    async def projeto_exists(self, projeto_id: str) -> bool:
        return self.projeto_exists_value

    async def ponto_exists(self, ponto_id: str) -> bool:
        return self.ponto_exists_value

    async def get_projeto_id_by_ponto(self, ponto_id: str) -> str | None:
        return PROJETO_ID

    async def user_can_access_projeto(self, projeto_id: str, user_id: str) -> bool:
        return self.can_access_projeto_value

    async def user_can_access_ponto(self, ponto_id: str, user_id: str) -> bool:
        return self.can_access_ponto_value

    async def save_ponto(self, projeto_id: str, ponto: str, tipo_poste: str, modelo_poste: str) -> str | None:
        return PONTO_ID

    async def save_calculo_snapshot(self, ponto_id: str, niveis: list[dict[str, Any]], resultado: dict[str, Any]) -> bool:
        return self.save_snapshot_value

    async def get_calculo_snapshot(self, ponto_id: str) -> dict[str, Any] | None:
        return self.snapshot_payload


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    async def _noop_async(*args: Any, **kwargs: Any) -> None:
        return None

    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("AUTH_JWT_SECRET", "test-jwt-secret-for-contract-tests")
    monkeypatch.setenv("AUTH_REQUIRE_JWT_FOR_MUTATIONS", "false")

    # Isolate contract tests from startup infra/auth hard requirements.
    monkeypatch.setattr(api_main, "validate_auth_config", lambda: None)
    monkeypatch.setattr(api_main, "initialize_db_pool", _noop_async)
    monkeypatch.setattr(api_main, "get_cache_manager", _noop_async)
    monkeypatch.setattr(api_main.db_pool, "close", _noop_async)

    app.dependency_overrides = {}
    with TestClient(app) as tc:
        yield tc
    app.dependency_overrides = {}


def _jwt_user() -> CurrentUser:
    return CurrentUser(user_id=USER_A_ID, role="user", auth_source="jwt", claims={})


def _projeto_payload() -> dict[str, Any]:
    return {
        "orgao": "TEST_ORGAO",
        "ns": "NS-CONTRACT",
        "nome": "ProjetoContrato",
        "endereco": "Rua Contrato, 123",
        "estudado_por": "Contrato Bot",
        "matricula": "9999",
        "data_estudo": "2026-03-24",
    }


def _ponto_payload() -> dict[str, Any]:
    return {
        "ponto": "P001",
        "tipo_poste": "DT",
        "modelo_poste": "11/600",
    }


def _travessias() -> list[dict[str, Any]]:
    return [
        {
            "posicao": pos,
            "tipo_rede": "",
            "tipo_cabo": "",
            "vao": 0,
            "flecha": 0,
            "angulo": 0,
            "qtd_ligacoes": 0,
            "qtd_cabos": 0,
        }
        for pos in (1, 2, 3, 4)
    ]


def _snapshot_payload(ponto_id: str) -> dict[str, Any]:
    niveis = [
        {"nivel": "MT1", "altura_poste": 11, "altura_ancoragem": 9.2, "travessias": _travessias()},
        {"nivel": "MT2", "altura_poste": 10.5, "altura_ancoragem": 8.7, "travessias": _travessias()},
        {"nivel": "BT", "altura_poste": 9, "altura_ancoragem": 7.5, "travessias": _travessias()},
        {"nivel": "BTZ", "altura_poste": 1.5, "altura_ancoragem": 1, "travessias": _travessias()},
        {"nivel": "RAL", "altura_poste": 8, "altura_ancoragem": 6.5, "travessias": _travessias()},
    ]
    return {
        "ponto_id": ponto_id,
        "niveis": niveis,
        "resultado": {
            "mt1_tracao": 10,
            "mt1_angulo": 5,
            "mt2_tracao": 0,
            "mt2_angulo": 0,
            "bt_tracao": 0,
            "bt_angulo": 0,
            "btz_tracao": 0,
            "btz_angulo": 0,
            "ral_tracao": 0,
            "ral_angulo": 0,
            "total_tracao": 10,
            "total_angulo": 5,
            "poste_ecc": 1,
            "texto_mt1": "",
            "texto_mt2": "",
            "texto_bt": "",
            "texto_btz": "",
            "texto_ral": "",
            "texto_total": "Total final: 10 daN @ 5°",
        },
    }


def _install_auth_override() -> None:
    app.dependency_overrides[projetos_router.require_mutation_identity] = _jwt_user


def _install_supabase_override(stub: SupabaseStub) -> None:
    app.dependency_overrides[projetos_router.get_supabase_dependency] = lambda: stub


def test_contract_401_projetos_requires_jwt_when_enforced(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_REQUIRE_JWT_FOR_MUTATIONS", "true")

    response = client.post("/api/projetos", json=_projeto_payload())

    assert response.status_code == 401
    assert response.json()["detail"] == "JWT obrigatorio para operacoes de escrita"


def test_contract_404_create_ponto_when_project_not_found(client: TestClient) -> None:
    stub = SupabaseStub()
    stub.projeto_exists_value = False
    _install_auth_override()
    _install_supabase_override(stub)

    response = client.post(f"/api/projetos/{PROJETO_ID}/pontos", json=_ponto_payload())

    assert response.status_code == 404
    assert response.headers.get("X-Operation-ID")


def test_contract_403_create_ponto_when_forbidden(client: TestClient) -> None:
    stub = SupabaseStub()
    stub.projeto_exists_value = True
    stub.can_access_projeto_value = False
    _install_auth_override()
    _install_supabase_override(stub)

    response = client.post(f"/api/projetos/{PROJETO_ID}/pontos", json=_ponto_payload())

    assert response.status_code == 403
    assert response.headers.get("X-Operation-ID")


def test_contract_422_salvar_calculo_when_payload_point_mismatch(client: TestClient) -> None:
    stub = SupabaseStub()
    _install_auth_override()
    _install_supabase_override(stub)

    payload = _snapshot_payload(PONTO_ID)
    payload["ponto_id"] = "33333333-3333-3333-3333-333333333333"

    response = client.post(f"/api/pontos/{PONTO_ID}/calculo", json=payload)

    assert response.status_code == 422
    assert response.headers.get("X-Operation-ID")


def test_contract_404_snapshot_when_ponto_missing(client: TestClient) -> None:
    stub = SupabaseStub()
    stub.ponto_exists_value = False
    _install_auth_override()
    _install_supabase_override(stub)

    response = client.get(f"/api/pontos/{PONTO_ID}/snapshot")

    assert response.status_code == 404
    assert response.headers.get("X-Operation-ID")


def test_contract_403_snapshot_when_forbidden(client: TestClient) -> None:
    stub = SupabaseStub()
    stub.can_access_ponto_value = False
    _install_auth_override()
    _install_supabase_override(stub)

    response = client.get(f"/api/pontos/{PONTO_ID}/snapshot")

    assert response.status_code == 403
    assert response.headers.get("X-Operation-ID")


def test_contract_404_snapshot_when_absent(client: TestClient) -> None:
    stub = SupabaseStub()
    stub.snapshot_payload = None
    _install_auth_override()
    _install_supabase_override(stub)

    response = client.get(f"/api/pontos/{PONTO_ID}/snapshot")

    assert response.status_code == 404
    assert response.headers.get("X-Operation-ID")


def test_contract_200_snapshot_when_present(client: TestClient) -> None:
    stub = SupabaseStub()
    stub.snapshot_payload = {
        "ponto_id": PONTO_ID,
        "niveis": [{"nivel": "MT1", "travessias": [{"posicao": 1}, {"posicao": 2}, {"posicao": 3}, {"posicao": 4}]}],
        "resultado": {"total_tracao": 10, "total_angulo": 5, "texto_total": "Total final: 10 daN @ 5°"},
    }
    _install_auth_override()
    _install_supabase_override(stub)

    response = client.get(f"/api/pontos/{PONTO_ID}/snapshot")

    assert response.status_code == 200
    assert response.headers.get("X-Operation-ID")
    data = response.json()
    assert data["ponto_id"] == PONTO_ID
    assert data["resultado"]["total_tracao"] == 10
