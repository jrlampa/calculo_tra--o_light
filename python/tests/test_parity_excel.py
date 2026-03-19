"""Parity tests – compare Python output against evaluated Excel values.

The "golden" values are taken directly from the workbook's data_only
evaluation (i.e. the last-calculated cached result when the file was saved).

Workbook file: AP COSMO LDA NOVA 03 - PROJETO 5 - POSTE 1D.xlsm
SHA-256 prefix: d7f81d608b39179f  (see artifacts/manifest.json)

Verified golden values:
  MT1   217 daN @ 177°
  MT2   171 daN @  90°
  BT    165 daN @  60°
  BTZ     0 daN @   0°   (no BTZero data in this project)
  RAL     0 daN @   0°   (no Ramais data in this project)
  TOTAL 374 daN @ 112°
  Poste eccentricity: 20.09 daN

Run with:
    cd python
    python -m pytest tests/ -v
"""
from __future__ import annotations

import sys
import os

import pytest

# Allow  python/  to be on the path when running pytest from python/
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from translated.ponto_blocks import (
    BTTraversalInput,
    BTZeroTraversalInput,
    MTTraversalInput,
    RamaisTraversalInput,
    calcular_polo,
)


# ── Golden values from Cosmo LDA project ──────────────────────────────────

# Exact evaluated values from openpyxl data_only read
GOLDEN = {
    "MT1_resultante":   217.37,   # C32
    "MT1_f_tip":        217.0,    # F33 TEXT(x,0) = 217
    "MT1_angulo":       177.0,    # F34 TEXT(x,0) = 177
    "MT2_resultante":   192.22,   # C58
    "MT2_f_tip":        171.0,    # F59 → 171.33 → TEXT = 171
    "MT2_angulo":        90.0,    # F60
    "BT_resultante":    217.37,   # C84 = C32
    "BT_f_tip":         165.0,    # F85 → 165.39 → TEXT = 165
    "BT_angulo":         60.0,    # F86 → 60.26 → TEXT = 60
    "TOTAL":            373.67,   # C140
    "TOTAL_angulo":     112.0,    # C141 TEXT(x,0) = 112
    "POSTE_ECC":         20.09,   # C149
}

# Tolerance (daN) – allows for intermediate float vs Excel ROUND differences
TOL = 0.5  # 0.5 daN ≈ 0.2 % of 217 daN


# ── Cosmo LDA input data ───────────────────────────────────────────────────

def _cosmo_inputs():
    """Return the four MT1/MT2/BT/Btz/Ral input lists for the Cosmo LDA project."""

    # ── MT1 (rows 12-18)  –  2 active traversals ──────────────────────────
    mt1 = [
        MTTraversalInput(           # T1 – C column
            tipo_rede="Convencional",
            tipo_cabo="397MCM-CA, Nu",
            vao=33.0,
            flecha=0.5,
            angulo=0.0,
            altura_poste=11.0,
              altura_ancoragem=9.2,
        ),
        MTTraversalInput(           # T2 – F column
            tipo_rede="Convencional",
            tipo_cabo="397MCM-CA, Nu",
            vao=40.0,
            flecha=0.5,
            angulo=179.0,
            altura_poste=11.0,
              altura_ancoragem=9.2,
        ),
        MTTraversalInput(),         # T3 inactive
        MTTraversalInput(),         # T4 inactive
    ]

    # ── MT2 (rows 38-44)  –  2 active traversals ──────────────────────────
    mt2 = [
        MTTraversalInput(           # T1
            tipo_rede="Compacta",
                tipo_cabo="397MCM-CA, XLPE, 13,8 kV",
            vao=27.0,
            flecha=0.5,
            angulo=11.0,
            altura_poste=11.0,
            altura_ancoragem=8.2,
        ),
        MTTraversalInput(           # T2
            tipo_rede="Compacta",
                tipo_cabo="397MCM-CA, XLPE, 13,8 kV",
                vao=27.0,
            flecha=0.5,
            angulo=169.0,
            altura_poste=11.0,
            altura_ancoragem=8.2,
        ),
        MTTraversalInput(),
        MTTraversalInput(),
    ]

    # ── BT  (rows 64-70)  –  3 active traversals ──────────────────────────
    # T1 geometry/cable comes from MT1 T1; only alturaAncoragem is BT's own.
    bt = [
        BTTraversalInput(           # T1 – C col (C66=C14, real cable from MT1)
            tipo_rede="Multiplexada",
            tipo_cabo="70mm², MTX-BT ",   # informational; calc uses MT1 T1 cable
            altura_ancoragem=7.0,
        ),
        BTTraversalInput(           # T2 – F col  (F66=F14 geometry from MT1 T2)
            tipo_rede="Multiplexada",
            tipo_cabo="70mm², MTX-BT ",
            altura_ancoragem=7.0,
        ),
        BTTraversalInput(           # T3 – I col  fully independent
            tipo_rede="Multiplexada",
            tipo_cabo="70mm², MTX-BT ",
            vao=20.0,
            flecha=0.5,
            angulo=85.0,
            altura_poste=11.0,
            altura_ancoragem=7.0,
        ),
        BTTraversalInput(),         # T4 inactive
    ]

    btz = [BTZeroTraversalInput() for _ in range(4)]   # all inactive
    ral = [RamaisTraversalInput() for _ in range(4)]   # all inactive

    return mt1, mt2, bt, btz, ral


# ── Tests ──────────────────────────────────────────────────────────────────

def test_mt1_resultante():
    mt1, mt2, bt, btz, ral = _cosmo_inputs()
    out = calcular_polo(mt1, mt2, bt, btz, ral)
    assert abs(out.mt1.resultante - GOLDEN["MT1_resultante"]) < TOL, (
        f"MT1 resultante: got {out.mt1.resultante:.2f}, expected {GOLDEN['MT1_resultante']}"
    )


def test_mt1_angulo():
    mt1, mt2, bt, btz, ral = _cosmo_inputs()
    out = calcular_polo(mt1, mt2, bt, btz, ral)
    # text output rounds to 0 decimals; allow ±1°
    assert abs(round(out.mt1.angulo) - GOLDEN["MT1_angulo"]) <= 1, (
        f"MT1 angulo: got {out.mt1.angulo:.1f}, expected {GOLDEN['MT1_angulo']}"
    )


def test_mt1_f_tip():
    mt1, mt2, bt, btz, ral = _cosmo_inputs()
    out = calcular_polo(mt1, mt2, bt, btz, ral)
    assert abs(out.mt1.f_tip - 217.37) < TOL


def test_mt2_resultante():
    mt1, mt2, bt, btz, ral = _cosmo_inputs()
    out = calcular_polo(mt1, mt2, bt, btz, ral)
    assert abs(out.mt2.resultante - GOLDEN["MT2_resultante"]) < TOL


def test_mt2_angulo():
    mt1, mt2, bt, btz, ral = _cosmo_inputs()
    out = calcular_polo(mt1, mt2, bt, btz, ral)
    assert abs(round(out.mt2.angulo) - GOLDEN["MT2_angulo"]) <= 1


def test_bt_resultante_equals_mt1():
    """C84 = C32: BT resultante must equal MT1 resultante."""
    mt1, mt2, bt, btz, ral = _cosmo_inputs()
    out = calcular_polo(mt1, mt2, bt, btz, ral)
    assert out.bt.resultante == out.mt1.resultante, (
        f"BT resultante ({out.bt.resultante}) ≠ MT1 resultante ({out.mt1.resultante})"
    )


def test_bt_f_tip():
    mt1, mt2, bt, btz, ral = _cosmo_inputs()
    out = calcular_polo(mt1, mt2, bt, btz, ral)
    assert abs(out.bt.f_tip - 165.39) < TOL


def test_bt_angulo():
    mt1, mt2, bt, btz, ral = _cosmo_inputs()
    out = calcular_polo(mt1, mt2, bt, btz, ral)
    assert abs(round(out.bt.angulo) - GOLDEN["BT_angulo"]) <= 1


def test_poste_ecc():
    mt1, mt2, bt, btz, ral = _cosmo_inputs()
    out = calcular_polo(
        mt1, mt2, bt, btz, ral,
        tipo_poste="Concreto circular",
        modelo_poste="11 m / 600 daN",
    )
    assert abs(out.poste_ecc - GOLDEN["POSTE_ECC"]) < 0.05


def test_total_tracao():
    mt1, mt2, bt, btz, ral = _cosmo_inputs()
    out = calcular_polo(
        mt1, mt2, bt, btz, ral,
        tipo_poste="Concreto circular",
        modelo_poste="11 m / 600 daN",
    )
    assert abs(out.total_tracao - GOLDEN["TOTAL"]) < TOL * 2, (
        f"Total: got {out.total_tracao:.2f}, expected {GOLDEN['TOTAL']}"
    )


def test_total_angulo():
    mt1, mt2, bt, btz, ral = _cosmo_inputs()
    out = calcular_polo(
        mt1, mt2, bt, btz, ral,
        tipo_poste="Concreto circular",
        modelo_poste="11 m / 600 daN",
    )
    assert abs(round(out.total_angulo) - GOLDEN["TOTAL_angulo"]) <= 2


def test_text_outputs():
    mt1, mt2, bt, btz, ral = _cosmo_inputs()
    out = calcular_polo(
        mt1, mt2, bt, btz, ral,
        tipo_poste="Concreto circular",
        modelo_poste="11 m / 600 daN",
    )
    assert "217" in out.texto_mt1 or "217" in out.texto_mt1
    assert "171" in out.texto_mt2
    assert "165" in out.texto_bt
    assert "374" in out.texto_total or "373" in out.texto_total
