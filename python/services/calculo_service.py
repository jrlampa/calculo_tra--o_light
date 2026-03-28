"""Service layer for pole-traction calculations.

Encapsulates all mapping and assembly logic that previously lived directly
inside the ``/calcular`` router, keeping the router thin (validate → call
service → return response).
"""

from __future__ import annotations

import math
import logging
from typing import Sequence

from api.schemas import (
    BTTraversalIn,
    BTZeroTraversalIn,
    CalculoInput,
    CalculoOutput,
    LevelResultOut,
    MTTraversalIn,
    RamaisTraversalIn,
    VetorOut,
)
from translated.ponto_blocks import (
    BTTraversalInput,
    BTZeroTraversalInput,
    MTTraversalInput,
    RamaisTraversalInput,
    calcular_polo,
)

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


# ── Output assembler ─────────────────────────────────────────────────────────

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


# ── Service ──────────────────────────────────────────────────────────────────

class CalculoService:
    """Orchestrates pole-traction calculation.

    Responsibilities:
    * Map API schema objects to domain dataclasses.
    * Delegate computation to ``translated.ponto_blocks.calcular_polo``.
    * Assemble the ``CalculoOutput`` response.

    The router only needs to call :meth:`calcular` and handle exceptions.
    """

    def calcular(self, inp: CalculoInput) -> CalculoOutput:
        """Run traction calculation and return a structured output.

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


# Singleton – routers import this directly.
calculo_service = CalculoService()
