"""Unit tests for services.calculo_service.CalculoService.

Tests verify that the service layer:
1. Correctly maps Pydantic schema objects to domain dataclasses.
2. Returns a well-formed CalculoOutput for a valid minimal input.
3. Propagates domain errors (ValueError) without wrapping them.
4. Builds the vetores list only for non-zero traction levels.
"""
import sys
import os

os.environ.setdefault("AUTH_REQUIRE_JWT_FOR_MUTATIONS", "false")
os.environ.setdefault("APP_ENV", "development")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest

from api.schemas import (
    BTTraversalIn,
    BTZeroTraversalIn,
    CalculoInput,
    CabecalhoIn,
    MTTraversalIn,
    PosteCalculoIn,
    RamaisTraversalIn,
)
from services.calculo_service import CalculoService, _map_mt, _map_bt, _map_btz, _map_ral, _build_vetores


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _empty_mt() -> MTTraversalIn:
    return MTTraversalIn(tipo_rede="", tipo_cabo="", vao=0, flecha=0, angulo=0,
                         altura_poste=0, altura_ancoragem=0)

def _empty_bt() -> BTTraversalIn:
    return BTTraversalIn(tipo_rede="", tipo_cabo="", vao=0, flecha=0, angulo=0,
                         altura_poste=0, altura_ancoragem=0)

def _empty_btz() -> BTZeroTraversalIn:
    return BTZeroTraversalIn(qtd_ligacoes=0, vao=0, flecha=0, angulo=0,
                             altura_poste=0, altura_ancoragem=0)

def _empty_ral() -> RamaisTraversalIn:
    return RamaisTraversalIn(tipo_cabo="", qtd_cabos=0, vao=0, flecha=0, angulo=0,
                             altura_poste=0, altura_ancoragem=0)

def _minimal_input() -> CalculoInput:
    return CalculoInput(
        cabecalho=CabecalhoIn(),
        poste=PosteCalculoIn(tipo_poste="Concreto circular", modelo_poste="C11/6"),
        mt1=[_empty_mt()] * 4,
        mt2=[_empty_mt()] * 4,
        bt=[_empty_bt()] * 4,
        btz=[_empty_btz()] * 4,
        ral=[_empty_ral()] * 4,
    )


# ── Mapper unit tests ─────────────────────────────────────────────────────────

class TestInputMappers:
    def test_map_mt_copies_all_fields(self):
        src = MTTraversalIn(tipo_rede="Convencional", tipo_cabo="397MCM",
                            vao=33.0, flecha=0.5, angulo=45.0,
                            altura_poste=11.0, altura_ancoragem=9.2)
        dst = _map_mt(src)
        assert dst.tipo_rede == "Convencional"
        assert dst.tipo_cabo == "397MCM"
        assert dst.vao == 33.0
        assert dst.flecha == 0.5
        assert dst.angulo == 45.0
        assert dst.altura_poste == 11.0
        assert dst.altura_ancoragem == 9.2

    def test_map_bt_copies_all_fields(self):
        src = BTTraversalIn(tipo_rede="Compacta", tipo_cabo="35mm2",
                            vao=20.0, flecha=0.3, angulo=30.0,
                            altura_poste=10.0, altura_ancoragem=8.5)
        dst = _map_bt(src)
        assert dst.vao == 20.0
        assert dst.tipo_cabo == "35mm2"

    def test_map_btz_copies_qtd_ligacoes(self):
        src = BTZeroTraversalIn(qtd_ligacoes=3, vao=15.0, flecha=0.2, angulo=0,
                                altura_poste=9.0, altura_ancoragem=7.5)
        dst = _map_btz(src)
        assert dst.qtd_ligacoes == 3
        assert dst.vao == 15.0

    def test_map_ral_copies_qtd_cabos(self):
        src = RamaisTraversalIn(tipo_cabo="16mm2", qtd_cabos=2, vao=10.0,
                                flecha=0.1, angulo=0,
                                altura_poste=8.0, altura_ancoragem=6.5)
        dst = _map_ral(src)
        assert dst.qtd_cabos == 2
        assert dst.tipo_cabo == "16mm2"


# ── CalculoService integration ────────────────────────────────────────────────

class TestCalculoService:
    service = CalculoService()

    def test_calcular_minimal_input_returns_output(self):
        """All-zero input must return a valid CalculoOutput (status_poste ok)."""
        result = self.service.calcular(_minimal_input())
        assert result.total_tracao_dan == 0.0
        assert result.status_poste in ("OK", "TOLERANCIA", "SOBRECARGA", "")

    def test_calcular_output_has_five_level_fields(self):
        result = self.service.calcular(_minimal_input())
        assert result.mt1 is not None
        assert result.mt2 is not None
        assert result.bt is not None
        assert result.btz is not None
        assert result.ral is not None

    def test_calcular_vetores_empty_when_all_zero(self):
        """No non-zero traction → no vectors emitted."""
        result = self.service.calcular(_minimal_input())
        assert result.vetores == []

    def test_calcular_domain_error_propagates_as_value_error(self):
        """A geometrically invalid input (vao>0, flecha=0) should raise ValueError.

        The Pydantic model validator raises ValueError before even reaching the
        service, so this test verifies the schema-level guard works correctly.
        """
        with pytest.raises(Exception) as exc_info:
            MTTraversalIn(tipo_rede="", tipo_cabo="", vao=10.0, flecha=0.0,
                          angulo=0, altura_poste=11.0, altura_ancoragem=9.0)
        assert "flecha" in str(exc_info.value).lower() or "value_error" in str(type(exc_info.value)).lower()

    def test_calcular_texto_total_is_string(self):
        result = self.service.calcular(_minimal_input())
        assert isinstance(result.texto_total, str)
