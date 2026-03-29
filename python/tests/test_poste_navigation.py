"""Tests for Poste aggregate navigation helpers and the new API schemas.

Verifies that:
1. obter_condutores() returns one entry per nivel × travessia (5 × 4 = 20).
2. obter_condutores() entries contain all expected fields.
3. perfil() returns correct structural fields.
4. perfil() condutores_ativos only includes travessias with vao > 0.
5. perfil() ultimo_calculo is None when no calculations exist.
6. TravessiaUpdateIn rejects negative vao/flecha and angulo ≥ 360.
7. TravessiaUpdateIn accepts valid defaults.
8. CondutorOut validates field types.
"""
import sys
import os

os.environ.setdefault("AUTH_REQUIRE_JWT_FOR_MUTATIONS", "false")
os.environ.setdefault("APP_ENV", "development")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest

from pydantic import ValidationError

from api.schemas import CondutorOut, TravessiaUpdateIn
from domain.aggregates import Poste
from domain.entities import Nivel, Travessia
from domain.value_objects import (
    CaboConductor,
    Condutor,
    Geometria,
    NivelEnum,
    ProjetoId,
    TipoPoste,
    TipoRede,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _travessia(posicao: int, vao: float = 0.0) -> Travessia:
    return Travessia(
        posicao=posicao,
        condutor=Condutor(
            tipo_rede=TipoRede.CIRCUITO,
            tipo_cabo=CaboConductor.CAA,
        ),
        geometria=Geometria(vao=vao, flecha=0.5, angulo=10.0),
    )


def _nivel(nivel_enum: NivelEnum, vao: float = 0.0) -> Nivel:
    return Nivel(
        nivel_enum=nivel_enum,
        altura_poste=11.0,
        altura_ancoragem=9.0,
        travessias=[_travessia(p, vao=vao) for p in range(1, 5)],
    )


def _poste(vao: float = 0.0) -> Poste:
    return Poste(
        projeto_id=ProjetoId(),
        numero="1",
        tipo_poste=TipoPoste.CONCRETO,
        modelo_poste="11/600",
        niveis=[_nivel(ne, vao=vao) for ne in NivelEnum],
    )


# ── obter_condutores() ────────────────────────────────────────────────────────

class TestObterCondutores:

    def test_returns_20_entries(self):
        """5 niveis × 4 travessias = 20 total entries."""
        poste = _poste()
        condutores = poste.obter_condutores()
        assert len(condutores) == 20

    def test_each_entry_has_required_keys(self):
        """Each entry must expose nivel, posicao, tipo_rede, tipo_cabo, vao, flecha, angulo."""
        required = {"nivel", "posicao", "tipo_rede", "tipo_cabo", "vao", "flecha", "angulo"}
        for entry in _poste().obter_condutores():
            assert required.issubset(entry.keys()), f"Missing keys in {entry}"

    def test_nivel_values_cover_all_five(self):
        """All five NivelEnum values should appear."""
        niveis_in_result = {c["nivel"] for c in _poste().obter_condutores()}
        expected = {ne.value for ne in NivelEnum}
        assert niveis_in_result == expected

    def test_posicao_values_are_1_to_4(self):
        """Positions per nivel must be 1, 2, 3, 4."""
        for nivel_value in {c["nivel"] for c in _poste().obter_condutores()}:
            posicoes = sorted(
                c["posicao"]
                for c in _poste().obter_condutores()
                if c["nivel"] == nivel_value
            )
            assert posicoes == [1, 2, 3, 4]

    def test_vao_reflects_travessia_geometry(self):
        """vao in each entry must match the Travessia geometria.vao."""
        poste = _poste(vao=42.5)
        for entry in poste.obter_condutores():
            assert entry["vao"] == 42.5


# ── perfil() ─────────────────────────────────────────────────────────────────

class TestPerfil:

    def test_perfil_contains_identity_fields(self):
        poste = _poste()
        perfil = poste.perfil()
        assert perfil["numero"] == "1"
        assert perfil["tipo_poste"] == TipoPoste.CONCRETO
        assert perfil["modelo_poste"] == "11/600"
        assert "id" in perfil
        assert "projeto_id" in perfil

    def test_perfil_condutores_ativos_empty_when_no_vao(self):
        """When all traversals have vao=0, condutores_ativos should be empty."""
        poste = _poste(vao=0.0)
        assert poste.perfil()["condutores_ativos"] == []

    def test_perfil_condutores_ativos_populated_when_vao_set(self):
        """All 20 traversals with vao=15.0 should appear in condutores_ativos."""
        poste = _poste(vao=15.0)
        assert len(poste.perfil()["condutores_ativos"]) == 20

    def test_perfil_ultimo_calculo_none_when_no_calculos(self):
        poste = _poste()
        assert poste.perfil()["ultimo_calculo"] is None


# ── TravessiaUpdateIn ────────────────────────────────────────────────────────

class TestTravessiaUpdateIn:

    def test_valid_defaults(self):
        inp = TravessiaUpdateIn()
        assert inp.tipo_rede == "circuito"
        assert inp.tipo_cabo == "CAA"
        assert inp.vao == 0.0
        assert inp.flecha == 0.0
        assert inp.angulo == 0.0

    def test_valid_values(self):
        inp = TravessiaUpdateIn(tipo_rede="ramificacao", tipo_cabo="AACSR", vao=50.0, flecha=1.2, angulo=30.0)
        assert inp.vao == 50.0
        assert inp.angulo == 30.0

    def test_negative_vao_rejected(self):
        with pytest.raises(ValidationError):
            TravessiaUpdateIn(vao=-1.0)

    def test_negative_flecha_rejected(self):
        with pytest.raises(ValidationError):
            TravessiaUpdateIn(flecha=-0.1)

    def test_angulo_360_rejected(self):
        with pytest.raises(ValidationError):
            TravessiaUpdateIn(angulo=360.0)

    def test_angulo_359_accepted(self):
        inp = TravessiaUpdateIn(angulo=359.9)
        assert inp.angulo == 359.9


# ── CondutorOut ───────────────────────────────────────────────────────────────

class TestCondutorOut:

    def test_valid_condutor_out(self):
        c = CondutorOut(
            nivel="BT",
            posicao=2,
            tipo_rede="circuito",
            tipo_cabo="CAA",
            vao=30.0,
            flecha=0.8,
            angulo=15.0,
        )
        assert c.nivel == "BT"
        assert c.posicao == 2

    def test_posicao_below_1_rejected(self):
        with pytest.raises(ValidationError):
            CondutorOut(nivel="BT", posicao=0, tipo_rede="c", tipo_cabo="CAA", vao=0, flecha=0, angulo=0)

    def test_posicao_above_4_rejected(self):
        with pytest.raises(ValidationError):
            CondutorOut(nivel="BT", posicao=5, tipo_rede="c", tipo_cabo="CAA", vao=0, flecha=0, angulo=0)
