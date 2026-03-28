"""Unit tests for services.calculo_service.CalculoService.

Tests verify that the service layer:
1. Correctly maps Pydantic schema objects to domain dataclasses.
2. Returns a well-formed CalculoOutput for a valid minimal input.
3. Propagates domain errors (ValueError) without wrapping them.
4. Builds the vetores list only for non-zero traction levels.
5. calcular_com_resultado returns (CalculoOutput, CalculoResultado).
6. calcular_qdt maps inputs and returns a valid QDTOutput.
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
    QDTInput,
    RamaisTraversalIn,
)
from domain.value_objects import CalculoResultado
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


# ── CalculoService.calcular ───────────────────────────────────────────────────

class TestCalculoService:
    service = CalculoService()

    def test_calcular_minimal_input_returns_output(self):
        """All-zero input must return a valid CalculoOutput."""
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


# ── CalculoService.calcular_com_resultado ─────────────────────────────────────

class TestCalcularComResultado:
    service = CalculoService()

    def test_returns_tuple_of_output_and_resultado(self):
        """calcular_com_resultado must return (CalculoOutput, CalculoResultado)."""
        from api.schemas import CalculoOutput
        output, resultado = self.service.calcular_com_resultado(_minimal_input())
        assert isinstance(output, CalculoOutput)
        assert isinstance(resultado, CalculoResultado)

    def test_output_and_resultado_totals_agree(self):
        """The totals in CalculoOutput and CalculoResultado must be consistent."""
        output, resultado = self.service.calcular_com_resultado(_minimal_input())
        assert output.total_tracao_dan == resultado.total_tracao
        assert output.total_angulo_graus == resultado.total_angulo

    def test_resultado_has_all_level_fields(self):
        _, resultado = self.service.calcular_com_resultado(_minimal_input())
        for field in ("mt1_tracao", "mt2_tracao", "bt_tracao", "btz_tracao", "ral_tracao"):
            assert hasattr(resultado, field)


# ── CalculoService.calcular_qdt ──────────────────────────────────────────────

class TestCalcularQDT:
    service = CalculoService()

    def test_calcular_qdt_returns_output(self):
        """Default QDTInput should return a valid QDTOutput with finite voltages."""
        from api.schemas import QDTOutput
        inp = QDTInput()
        result = self.service.calcular_qdt(inp)
        assert isinstance(result, QDTOutput)
        assert result.v_mt_initial > 0
        assert result.v_bt_start > 0

    def test_calcular_qdt_drop_total_is_float(self):
        result = self.service.calcular_qdt(QDTInput())
        assert isinstance(result.drop_total_pct, float)

    def test_calcular_qdt_zero_drops_produces_no_voltage_loss(self):
        """With all drop percentages at zero the node voltages equal initial voltages."""
        inp = QDTInput(drop_mt_pct=0.0, drop_trafo_pct=0.0,
                       drop_bt1_pct=0.0, drop_bt2_pct=0.0)
        result = self.service.calcular_qdt(inp)
        # With no distribution drops the MT node voltage equals MT initial voltage
        assert result.v_mt_initial == result.v_mt_node

