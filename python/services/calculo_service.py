"""Service layer for pole-traction calculations.

Encapsulates all mapping and assembly logic that previously lived directly
inside the ``/calcular`` and ``/postes`` routers, keeping them thin
(validate → call service → return response).  Business logic lives here.
"""

from __future__ import annotations

import math
import logging
from typing import Tuple

from api.schemas import (
    BTTraversalIn,
    BTZeroTraversalIn,
    CalculoInput,
    CalculoOutput,
    LevelResultOut,
    MTTraversalIn,
    QDTInput,
    QDTOutput,
    RamaisTraversalIn,
    VetorOut,
)
from domain.value_objects import CalculoResultado
from translated.ponto_blocks import (
    BTTraversalInput,
    BTZeroTraversalInput,
    MTTraversalInput,
    RamaisTraversalInput,
    calcular_polo,
)
from translated.qdt_blocks import calcular_qdt, QDTInput as QDTLogicInput

logger = logging.getLogger(__name__)


# ── Input mappers ─────────────────────────────────────────────────────────────

def _map_mt(t: MTTraversalIn) -> MTTraversalInput:
    return MTTraversalInput(
        tipo_rede=t.tipo_rede,
        tipo_cabo=t.tipo_cabo,
        vao=t.vao,
        flecha=t.flecha,
        angulo=t.angulo,
        altura_poste=t.altura_poste,
        altura_ancoragem=t.altura_ancoragem,
    )


def _map_bt(t: BTTraversalIn) -> BTTraversalInput:
    return BTTraversalInput(
        tipo_rede=t.tipo_rede,
        tipo_cabo=t.tipo_cabo,
        vao=t.vao,
        flecha=t.flecha,
        angulo=t.angulo,
        altura_poste=t.altura_poste,
        altura_ancoragem=t.altura_ancoragem,
    )


def _map_btz(t: BTZeroTraversalIn) -> BTZeroTraversalInput:
    return BTZeroTraversalInput(
        qtd_ligacoes=t.qtd_ligacoes,
        vao=t.vao,
        flecha=t.flecha,
        angulo=t.angulo,
        altura_poste=t.altura_poste,
        altura_ancoragem=t.altura_ancoragem,
    )


def _map_ral(t: RamaisTraversalIn) -> RamaisTraversalInput:
    return RamaisTraversalInput(
        tipo_cabo=t.tipo_cabo,
        qtd_cabos=t.qtd_cabos,
        vao=t.vao,
        flecha=t.flecha,
        angulo=t.angulo,
        altura_poste=t.altura_poste,
        altura_ancoragem=t.altura_ancoragem,
    )


# ── Output assemblers ────────────────────────────────────────────────────────

def _build_vetores(result) -> list[VetorOut]:
    """Build the vector list used by the clock-angle diagram."""
    level_defs = [
        ("MT1", result.mt1.f_tip, result.mt1.angulo),
        ("MT2", result.mt2.f_tip, result.mt2.angulo),
        ("BT",  result.bt.f_tip,  result.bt.angulo),
        ("BTZ", result.btz.f_tip, result.btz.angulo),
        ("RAL", result.ral.f_tip, result.ral.angulo),
    ]
    return [
        VetorOut(
            label=label,
            tracao_dan=f,
            angulo_graus=a,
            comp_x=f * math.cos(a * math.pi / 180),
            comp_y=f * math.sin(a * math.pi / 180),
        )
        for label, f, a in level_defs
        if f != 0
    ]


def _build_calculo_output(result) -> CalculoOutput:
    """Assemble ``CalculoOutput`` from a raw engine result."""
    return CalculoOutput(
        mt1=LevelResultOut(
            tracao_dan=result.mt1.f_tip,
            angulo_graus=result.mt1.angulo,
            resultante_raw=result.mt1.resultante,
            texto=result.texto_mt1,
        ),
        mt2=LevelResultOut(
            tracao_dan=result.mt2.f_tip,
            angulo_graus=result.mt2.angulo,
            resultante_raw=result.mt2.resultante,
            texto=result.texto_mt2,
        ),
        bt=LevelResultOut(
            tracao_dan=result.bt.f_tip,
            angulo_graus=result.bt.angulo,
            resultante_raw=result.bt.resultante,
            texto=result.texto_bt,
        ),
        btz=LevelResultOut(
            tracao_dan=result.btz.f_tip,
            angulo_graus=result.btz.angulo,
            resultante_raw=result.btz.resultante,
            texto=result.texto_btz,
        ),
        ral=LevelResultOut(
            tracao_dan=result.ral.f_tip,
            angulo_graus=result.ral.angulo,
            resultante_raw=result.ral.resultante,
            texto=result.texto_ral,
        ),
        total_tracao_dan=result.total_tracao,
        total_angulo_graus=result.total_angulo,
        texto_total=result.texto_total,
        vetores=_build_vetores(result),
        poste_ecc_dan=result.poste_ecc,
        status_poste=result.status_poste,
        resistencia_nominal=result.resistencia_nominal,
    )


def _build_calculo_resultado(result) -> CalculoResultado:
    """Build the domain ``CalculoResultado`` value object from a raw engine result."""
    return CalculoResultado(
        mt1_tracao=result.mt1.f_tip,
        mt1_angulo=result.mt1.angulo,
        mt2_tracao=result.mt2.f_tip,
        mt2_angulo=result.mt2.angulo,
        bt_tracao=result.bt.f_tip,
        bt_angulo=result.bt.angulo,
        btz_tracao=result.btz.f_tip,
        btz_angulo=result.btz.angulo,
        ral_tracao=result.ral.f_tip,
        ral_angulo=result.ral.angulo,
        total_tracao=result.total_tracao,
        total_angulo=result.total_angulo,
        poste_ecc=result.poste_ecc,
    )


# ── Service ──────────────────────────────────────────────────────────────────

class CalculoService:
    """Orchestrates pole-traction and voltage-drop calculations.

    Responsibilities:
    * Map API schema objects to domain dataclasses.
    * Delegate computation to the domain engine (``translated`` package).
    * Assemble structured response objects.

    Routers only need to call these methods and handle HTTP exceptions.
    """

    # ── Traction (polo) ──────────────────────────────────────────────────────

    def calcular(self, inp: CalculoInput) -> CalculoOutput:
        """Run traction calculation and return a ``CalculoOutput``.

        Raises:
            ValueError: domain-level error from the calculation engine.
            ZeroDivisionError / ArithmeticError: invalid geometry.
        """
        output, _ = self.calcular_com_resultado(inp)
        return output

    def calcular_com_resultado(
        self, inp: CalculoInput
    ) -> Tuple[CalculoOutput, CalculoResultado]:
        """Run traction calculation and return both the API output and the
        domain value object.

        Use this overload when the caller also needs to persist the raw result
        (e.g. the ``/postes/{id}/calcular`` endpoint).

        Returns:
            (CalculoOutput, CalculoResultado): the structured API response
            and the immutable domain value object carrying raw per-level
            traction figures, respectively.

        Raises:
            ValueError: domain-level error from the calculation engine.
            ZeroDivisionError / ArithmeticError: invalid geometry.
        """
        result = calcular_polo(
            mt1_inputs=[_map_mt(t) for t in inp.mt1],
            mt2_inputs=[_map_mt(t) for t in inp.mt2],
            bt_inputs=[_map_bt(t) for t in inp.bt],
            btz_inputs=[_map_btz(t) for t in inp.btz],
            ral_inputs=[_map_ral(t) for t in inp.ral],
            tipo_poste=inp.poste.tipo_poste,
            modelo_poste=inp.poste.modelo_poste,
        )
        return _build_calculo_output(result), _build_calculo_resultado(result)

    # ── Voltage drop (QDT) ───────────────────────────────────────────────────

    def calcular_qdt(self, inp: QDTInput) -> QDTOutput:
        """Run voltage-drop (QDT) calculation and return a ``QDTOutput``."""
        logic_in = QDTLogicInput(
            v_nominal_mt=inp.v_nominal_mt,
            v_nominal_bt=inp.v_nominal_bt,
            coef_perda=inp.coef_perda,
            reg_mt=inp.reg_mt,
            drop_mt_pct=inp.drop_mt_pct,
            drop_trafo_pct=inp.drop_trafo_pct,
            drop_bt1_pct=inp.drop_bt1_pct,
            drop_bt2_pct=inp.drop_bt2_pct,
        )
        res = calcular_qdt(logic_in)
        return QDTOutput(
            v_mt_initial=res.v_mt_initial,
            v_mt_node=res.v_mt_node,
            v_bt_start=res.v_bt_start,
            v_bt_node1=res.v_bt_node1,
            v_bt_node2=res.v_bt_node2,
            drop_total_pct=res.drop_total_pct,
        )


# Singleton – routers import this directly.
calculo_service = CalculoService()

