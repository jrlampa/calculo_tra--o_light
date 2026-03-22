"""Compatibility tests for projeto column contracts."""

from __future__ import annotations

import asyncio
from datetime import datetime
from uuid import uuid4

from models.projeto import Projeto
from repositories.projeto_repository import ProjetoRepository


class FakeDB:
    """Minimal async DB fake to validate generated SQL."""

    def __init__(self, column_names: list[str], row: dict):
        self.column_names = column_names
        self.row = row
        self.last_query = ""

    async def fetch_all(self, query: str, *args):
        self.last_query = query
        if "information_schema.columns" in query:
            return [{"column_name": name} for name in self.column_names]
        return [self.row]

    async def fetch_one(self, query: str, *args):
        self.last_query = query
        return self.row


def _sample_row_en() -> dict:
    now = datetime.utcnow()
    return {
        "id": uuid4(),
        "orgao": "Orgao A",
        "ns": "NS-001",
        "nome": "Projeto A",
        "endereco": "Endereco A",
        "estudado_por": "User A",
        "matricula": "123",
        "data_estudo": now,
        "owner_id": uuid4(),
        "total_pontos": 0,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None,
    }


def _sample_row_ptbr() -> dict:
    now = datetime.utcnow()
    return {
        "id": uuid4(),
        "orgao": "Orgao B",
        "ns": "NS-002",
        "nome": "Projeto B",
        "endereco": "Endereco B",
        "estudado_por": "User B",
        "matricula": "456",
        "data_estudo": now,
        "owner_id": uuid4(),
        "total_pontos": 0,
        "criado_em": now,
        "atualizado_em": now,
        "deletado_em": None,
    }


def test_model_accepts_ptbr_timestamp_columns() -> None:
    projeto = Projeto(**_sample_row_ptbr())
    assert projeto.created_at is not None
    assert projeto.updated_at is not None


def test_repository_get_uses_english_soft_delete_when_available() -> None:
    db = FakeDB(
        column_names=["created_at", "updated_at", "deleted_at"],
        row=_sample_row_en(),
    )
    repository = ProjetoRepository(db)

    asyncio.run(repository.get(uuid4()))

    assert "deleted_at IS NULL" in db.last_query


def test_repository_get_uses_ptbr_soft_delete_when_available() -> None:
    db = FakeDB(
        column_names=["criado_em", "atualizado_em", "deletado_em"],
        row=_sample_row_ptbr(),
    )
    repository = ProjetoRepository(db)

    asyncio.run(repository.get(uuid4()))

    assert "deletado_em IS NULL" in db.last_query
