"""Unit tests for PosteFactory — domain factory for Poste aggregate.

Verifies:
1. from_calculo_input() creates a valid PosteAggregate from CalculoInput.
2. from_calculo_input() maps numero from cabecalho.numero.
3. from_calculo_input() creates 5 niveis with 4 travessias each.
4. _parse_tipo_cabo() maps known strings to CaboConductor enum values.
5. _parse_tipo_rede() maps known strings to TipoRede enum values.
6. to_response_dict() serializes a PosteAggregate to a JSON-safe dict.
7. to_response_dict() includes nil-safe fields (origem_id, deletado_em).
"""
import sys
import os

os.environ.setdefault("AUTH_REQUIRE_JWT_FOR_MUTATIONS", "false")
os.environ.setdefault("APP_ENV", "development")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from uuid import uuid4

from api.schemas import (
    CalculoInput,
    CabecalhoIn,
    MTTraversalIn,
    BTTraversalIn,
    BTZeroTraversalIn,
    RamaisTraversalIn,
    PosteCalculoIn,
)
from domain.factories import PosteFactory
from domain.value_objects import CaboConductor, TipoRede, NivelEnum


# ──────────────────────── helpers ─────────────────────────────────────────────

def _mt_trav(**kwargs):
    defaults = dict(
        tipo_rede="Convencional",
        tipo_cabo="CAA",
        vao=30.0,
        flecha=0.5,
        angulo=10.0,
        altura_poste=11.0,
        altura_ancoragem=9.2,
    )
    defaults.update(kwargs)
    return MTTraversalIn(**defaults)


def _bt_trav(**kwargs):
    defaults = dict(
        tipo_rede="Convencional",
        tipo_cabo="CAA",
        vao=30.0,
        flecha=0.5,
        angulo=10.0,
        altura_poste=11.0,
        altura_ancoragem=9.2,
    )
    defaults.update(kwargs)
    return BTTraversalIn(**defaults)


def _btz_trav(**kwargs):
    defaults = dict(
        qtd_ligacoes=5,
        vao=30.0,
        flecha=0.5,
        angulo=10.0,
        altura_poste=11.0,
        altura_ancoragem=9.2,
    )
    defaults.update(kwargs)
    return BTZeroTraversalIn(**defaults)


def _ral_trav(**kwargs):
    defaults = dict(
        tipo_cabo="CAA",
        qtd_cabos=2,
        vao=30.0,
        flecha=0.5,
        angulo=10.0,
        altura_poste=11.0,
        altura_ancoragem=9.2,
    )
    defaults.update(kwargs)
    return RamaisTraversalIn(**defaults)


def _minimal_calculo_input(numero="P-01"):
    """Build a valid CalculoInput for factory tests."""
    travs_mt = [_mt_trav() for _ in range(4)]
    travs_bt = [_bt_trav() for _ in range(4)]
    travs_btz = [_btz_trav() for _ in range(4)]
    travs_ral = [_ral_trav() for _ in range(4)]

    return CalculoInput(
        cabecalho=CabecalhoIn(numero=numero),
        poste=PosteCalculoIn(tipo_poste="Concreto", modelo_poste="11/200"),
        mt1=travs_mt,
        mt2=travs_mt,
        bt=travs_bt,
        btz=travs_btz,
        ral=travs_ral,
    )


# ──────────────────────── from_calculo_input ──────────────────────────────────

class TestFromCalculoInput:
    def test_creates_valid_poste(self):
        inp = _minimal_calculo_input("P-05")
        projeto_id = uuid4()
        poste = PosteFactory.from_calculo_input(projeto_id, inp)

        assert poste is not None
        assert poste.numero == "P-05"
        assert poste.projeto_id.value == projeto_id

    def test_poste_has_five_niveis(self):
        inp = _minimal_calculo_input()
        poste = PosteFactory.from_calculo_input(uuid4(), inp)
        assert len(poste.niveis) == 5

    def test_each_nivel_has_four_travessias(self):
        inp = _minimal_calculo_input()
        poste = PosteFactory.from_calculo_input(uuid4(), inp)
        for nivel in poste.niveis:
            assert len(nivel.travessias) == 4

    def test_maps_tipo_poste_and_modelo_poste(self):
        inp = _minimal_calculo_input()
        poste = PosteFactory.from_calculo_input(uuid4(), inp)
        assert poste.tipo_poste == "Concreto"
        assert poste.modelo_poste == "11/200"

    def test_maps_altura_from_first_traversal(self):
        inp = _minimal_calculo_input()
        poste = PosteFactory.from_calculo_input(uuid4(), inp)
        mt1 = next(n for n in poste.niveis if n.nivel_enum == NivelEnum.MT1)
        assert mt1.altura_poste == 11.0
        assert mt1.altura_ancoragem == 9.2

    def test_uses_unknown_numero_when_cabecalho_numero_empty(self):
        inp = _minimal_calculo_input(numero="")
        poste = PosteFactory.from_calculo_input(uuid4(), inp)
        assert poste.numero == "UNKNOWN"

    def test_geometria_mapped_to_travessia(self):
        inp = _minimal_calculo_input()
        poste = PosteFactory.from_calculo_input(uuid4(), inp)
        mt1 = next(n for n in poste.niveis if n.nivel_enum == NivelEnum.MT1)
        trav1 = next(t for t in mt1.travessias if t.posicao == 1)
        assert trav1.geometria.vao == 30.0
        assert trav1.geometria.flecha == 0.5
        assert trav1.geometria.angulo == 10.0

    def test_poste_passes_validar(self):
        inp = _minimal_calculo_input()
        poste = PosteFactory.from_calculo_input(uuid4(), inp)
        poste.validar()  # must not raise


# ──────────────────────── _parse_tipo_cabo ────────────────────────────────────

class TestParseTipoCabo:
    def test_empty_string_defaults_to_caa(self):
        result = PosteFactory._parse_tipo_cabo("")
        assert result == CaboConductor.CAA

    def test_caa_exact(self):
        assert PosteFactory._parse_tipo_cabo("CAA") == CaboConductor.CAA

    def test_aacsr(self):
        assert PosteFactory._parse_tipo_cabo("AACSR") == CaboConductor.AACSR

    def test_aacsr_variant(self):
        assert PosteFactory._parse_tipo_cabo("397MCM-AACSR") == CaboConductor.AACSR

    def test_neutro(self):
        assert PosteFactory._parse_tipo_cabo("Neutro") == CaboConductor.NEUTRO

    def test_neutro_uppercase(self):
        assert PosteFactory._parse_tipo_cabo("NEUTRO") == CaboConductor.NEUTRO

    def test_terra(self):
        assert PosteFactory._parse_tipo_cabo("TERRA") == CaboConductor.TERRA

    def test_cu(self):
        assert PosteFactory._parse_tipo_cabo("CU") == CaboConductor.CU

    def test_al(self):
        assert PosteFactory._parse_tipo_cabo("AL") == CaboConductor.AL

    def test_unknown_defaults_to_caa(self):
        assert PosteFactory._parse_tipo_cabo("UNKNOWN_CABLE") == CaboConductor.CAA


# ──────────────────────── _parse_tipo_rede ────────────────────────────────────

class TestParseTipoRede:
    def test_empty_string_defaults_to_circuito(self):
        assert PosteFactory._parse_tipo_rede("") == TipoRede.CIRCUITO

    def test_circuito(self):
        assert PosteFactory._parse_tipo_rede("Circuito") == TipoRede.CIRCUITO

    def test_ramificacao(self):
        assert PosteFactory._parse_tipo_rede("Ramificação") == TipoRede.RAMIFICACAO

    def test_ramif_short(self):
        assert PosteFactory._parse_tipo_rede("RAMIF") == TipoRede.RAMIFICACAO

    def test_interligacao(self):
        assert PosteFactory._parse_tipo_rede("Interligação") == TipoRede.INTERLIGACAO

    def test_interlig_short(self):
        assert PosteFactory._parse_tipo_rede("INTERLIG") == TipoRede.INTERLIGACAO

    def test_unknown_defaults_to_circuito(self):
        assert PosteFactory._parse_tipo_rede("UNKNOWN") == TipoRede.CIRCUITO


# ──────────────────────── to_response_dict ────────────────────────────────────

class TestToResponseDict:
    def test_returns_dict_with_required_keys(self):
        inp = _minimal_calculo_input("P-10")
        poste = PosteFactory.from_calculo_input(uuid4(), inp)
        d = PosteFactory.to_response_dict(poste)

        assert "id" in d
        assert "projeto_id" in d
        assert "numero" in d
        assert "tipo_poste" in d
        assert "modelo_poste" in d
        assert "niveis" in d
        assert "origem_id" in d
        assert "criado_em" in d
        assert "deletado_em" in d

    def test_numero_preserved(self):
        inp = _minimal_calculo_input("P-10")
        poste = PosteFactory.from_calculo_input(uuid4(), inp)
        d = PosteFactory.to_response_dict(poste)
        assert d["numero"] == "P-10"

    def test_origem_id_is_none_for_new_poste(self):
        inp = _minimal_calculo_input()
        poste = PosteFactory.from_calculo_input(uuid4(), inp)
        d = PosteFactory.to_response_dict(poste)
        assert d["origem_id"] is None

    def test_deletado_em_is_none_for_active_poste(self):
        inp = _minimal_calculo_input()
        poste = PosteFactory.from_calculo_input(uuid4(), inp)
        d = PosteFactory.to_response_dict(poste)
        assert d["deletado_em"] is None

    def test_niveis_has_five_entries(self):
        inp = _minimal_calculo_input()
        poste = PosteFactory.from_calculo_input(uuid4(), inp)
        d = PosteFactory.to_response_dict(poste)
        assert len(d["niveis"]) == 5

    def test_nivel_has_travessias_list(self):
        inp = _minimal_calculo_input()
        poste = PosteFactory.from_calculo_input(uuid4(), inp)
        d = PosteFactory.to_response_dict(poste)
        for n in d["niveis"]:
            assert "travessias" in n
            assert len(n["travessias"]) == 4

    def test_id_is_string(self):
        inp = _minimal_calculo_input()
        poste = PosteFactory.from_calculo_input(uuid4(), inp)
        d = PosteFactory.to_response_dict(poste)
        assert isinstance(d["id"], str)
        assert isinstance(d["projeto_id"], str)
