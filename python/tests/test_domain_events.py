"""Unit tests for domain events (immutable records of what happened).

Verifies that:
1. Each event stores its fields correctly.
2. ``to_dict()`` serializes all required keys with correct types.
3. Events are immutable (frozen dataclasses).
4. Inheritance from DomainEvent works as expected.
"""
import sys
import os

os.environ.setdefault("AUTH_REQUIRE_JWT_FOR_MUTATIONS", "false")
os.environ.setdefault("APP_ENV", "development")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from datetime import datetime, UTC
from uuid import UUID, uuid4

from domain.events import (
    DomainEvent,
    ProjetoCriado,
    PosteCriado,
    NivelAtualizado,
    TravessiaAtualizada,
    CalculoSnapshot,
    CalculoDeletado,
    PosteVinculado,
    PosteDeletado,
    ProjetoDeletado,
)


# ──────────────────────── helpers ─────────────────────────────────────────────

def _base_kwargs(aggregate_id=None, aggregate_type="Test"):
    return {
        "event_id": uuid4(),
        "aggregate_id": aggregate_id or uuid4(),
        "aggregate_type": aggregate_type,
        "timestamp": datetime.now(UTC),
    }


# ──────────────────────── DomainEvent base ────────────────────────────────────

class TestDomainEvent:
    def test_to_dict_has_required_keys(self):
        evt = DomainEvent(**_base_kwargs())
        d = evt.to_dict()
        assert "event_id" in d
        assert "aggregate_id" in d
        assert "aggregate_type" in d
        assert "timestamp" in d
        assert "event_type" in d

    def test_to_dict_event_type_is_class_name(self):
        evt = DomainEvent(**_base_kwargs())
        assert evt.to_dict()["event_type"] == "DomainEvent"

    def test_to_dict_ids_are_strings(self):
        aid = uuid4()
        evt = DomainEvent(**_base_kwargs(aid))
        d = evt.to_dict()
        assert d["aggregate_id"] == str(aid)
        assert isinstance(d["event_id"], str)

    def test_event_is_immutable(self):
        evt = DomainEvent(**_base_kwargs())
        with pytest.raises((AttributeError, TypeError)):
            evt.aggregate_type = "Changed"  # type: ignore[misc]


# ──────────────────────── ProjetoCriado ───────────────────────────────────────

class TestProjetoCriado:
    def test_stores_fields(self):
        aid = uuid4()
        evt = ProjetoCriado(
            **_base_kwargs(aid, "Projeto"),
            nome="Proj A",
            owner_id="user-1",
            orgao="ENEL",
            ns="EN-001",
        )
        assert evt.nome == "Proj A"
        assert evt.owner_id == "user-1"

    def test_to_dict_includes_projeto_fields(self):
        evt = ProjetoCriado(
            **_base_kwargs("Projeto"),
            nome="Proj B",
            owner_id="u2",
            orgao="LIGHT",
            ns="LT-002",
        )
        d = evt.to_dict()
        assert d["nome"] == "Proj B"
        assert d["owner_id"] == "u2"
        assert d["orgao"] == "LIGHT"
        assert d["ns"] == "LT-002"
        assert d["event_type"] == "ProjetoCriado"


# ──────────────────────── PosteCriado ─────────────────────────────────────────

class TestPosteCriado:
    def test_to_dict_includes_poste_fields(self):
        proj_id = uuid4()
        evt = PosteCriado(
            **_base_kwargs("Poste"),
            projeto_id=proj_id,
            numero="P-01",
            tipo_poste="Concreto",
            modelo_poste="11/200",
        )
        d = evt.to_dict()
        assert d["numero"] == "P-01"
        assert d["tipo_poste"] == "Concreto"
        assert d["modelo_poste"] == "11/200"
        assert d["projeto_id"] == str(proj_id)
        assert d["event_type"] == "PosteCriado"


# ──────────────────────── NivelAtualizado ─────────────────────────────────────

class TestNivelAtualizado:
    def test_to_dict_includes_nivel_fields(self):
        evt = NivelAtualizado(
            **_base_kwargs("Poste"),
            nivel="MT1",
            altura_poste=11.0,
            altura_ancoragem=9.2,
        )
        d = evt.to_dict()
        assert d["nivel"] == "MT1"
        assert d["altura_poste"] == 11.0
        assert d["event_type"] == "NivelAtualizado"


# ──────────────────────── TravessiaAtualizada ─────────────────────────────────

class TestTravessiaAtualizada:
    def test_to_dict_includes_traversal_fields(self):
        evt = TravessiaAtualizada(
            **_base_kwargs("Poste"),
            nivel="BT",
            posicao=2,
            tipo_rede="Convencional",
            tipo_cabo="CAA",
            vao=40.0,
            flecha=1.2,
            angulo=15.0,
        )
        d = evt.to_dict()
        assert d["nivel"] == "BT"
        assert d["posicao"] == 2
        assert d["vao"] == 40.0
        assert d["tipo_cabo"] == "CAA"
        assert d["event_type"] == "TravessiaAtualizada"


# ──────────────────────── CalculoSnapshot ─────────────────────────────────────

class TestCalculoSnapshot:
    def test_to_dict_includes_calculo_fields(self):
        resultado = {"total_tracao_dan": 150.0}
        evt = CalculoSnapshot(
            **_base_kwargs("Poste"),
            status="saved",
            resultado_json=resultado,
        )
        d = evt.to_dict()
        assert d["status"] == "saved"
        assert d["resultado_json"] == resultado
        assert d["event_type"] == "CalculoSnapshot"

    def test_default_status_is_draft(self):
        evt = CalculoSnapshot(**_base_kwargs("Poste"))
        assert evt.status == "draft"


# ──────────────────────── CalculoDeletado ─────────────────────────────────────

class TestCalculoDeletado:
    def test_to_dict_razao(self):
        evt = CalculoDeletado(
            **_base_kwargs("Poste"),
            razao="user cancelled",
        )
        d = evt.to_dict()
        assert d["razao"] == "user cancelled"
        assert d["event_type"] == "CalculoDeletado"


# ──────────────────────── PosteVinculado ──────────────────────────────────────

class TestPosteVinculado:
    def test_to_dict_includes_lineage_fields(self):
        origem_proj = uuid4()
        evt = PosteVinculado(
            **_base_kwargs("Poste"),
            numero="P-A",
            origem_numero="P-X",
            origem_projeto_id=origem_proj,
        )
        d = evt.to_dict()
        assert d["numero"] == "P-A"
        assert d["origem_numero"] == "P-X"
        assert d["origem_projeto_id"] == str(origem_proj)
        assert d["event_type"] == "PosteVinculado"

    def test_to_dict_origem_projeto_id_none(self):
        evt = PosteVinculado(
            **_base_kwargs("Poste"),
            origem_projeto_id=None,
        )
        d = evt.to_dict()
        assert d["origem_projeto_id"] is None


# ──────────────────────── PosteDeletado ───────────────────────────────────────

class TestPosteDeletado:
    def test_to_dict_includes_poste_deletado_fields(self):
        evt = PosteDeletado(
            **_base_kwargs("Poste"),
            numero="P-DEL",
            razao="owner request",
        )
        d = evt.to_dict()
        assert d["numero"] == "P-DEL"
        assert d["razao"] == "owner request"
        assert d["event_type"] == "PosteDeletado"


# ──────────────────────── ProjetoDeletado ─────────────────────────────────────

class TestProjetoDeletado:
    def test_to_dict_includes_projeto_deletado_fields(self):
        evt = ProjetoDeletado(
            **_base_kwargs("Projeto"),
            nome="Antigo Projeto",
            razao="project closed",
        )
        d = evt.to_dict()
        assert d["nome"] == "Antigo Projeto"
        assert d["razao"] == "project closed"
        assert d["event_type"] == "ProjetoDeletado"
