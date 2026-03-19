"""Queda de Tensão (QDT) / Voltage Drop calculation engine.

Translates the load-based voltage drop chain from the 'Alocação % de tensão' sheet.
Reproduces calculations for MT, Transformer, and BT segments.
"""
from __future__ import annotations
from dataclasses import dataclass
import math

@dataclass
class QDTInput:
    v_nominal_mt: float = 13200.0  # L47
    v_nominal_bt: float = 220.0    # E48
    coef_perda: float = 75.0       # C48 (example: diversity/loss coefficient)
    reg_mt: float = 1.02           # O47 (e.g. 102% of nominal at start)
    drop_mt_pct: float = 3.5       # F48 (%)
    drop_trafo_pct: float = 4.5    # G48 (%)
    drop_bt1_pct: float = 5.0      # H48 (%)
    drop_bt2_pct: float = 1.5      # I48 (%)

@dataclass
class QDTResult:
    v_mt_initial: float
    v_mt_node: float
    v_bt_start: float
    v_bt_node1: float
    v_bt_node2: float
    drop_total_pct: float

def calcular_qdt(inp: QDTInput) -> QDTResult:
    """Execute the sequential voltage drop chain."""
    
    # 1. MT Initial (13464 in Excel case)
    v_mt_initial = inp.v_nominal_mt * inp.reg_mt
    
    # 2. MT Drop (F49 formula pattern)
    # F49 = ((100 - (F48 * C48 / 100)) / 100) * v_initial
    # In Excel, F48 is 3.5%, C48 is 75. 
    # Drop = 3.5 * 0.75 = 2.625%. Efficiency = 97.375%
    v_mt_node = v_mt_initial * (1.0 - (inp.drop_mt_pct * inp.coef_perda / 10000.0))
    
    # 3. Transformer Drop & Base Change (G49 formula pattern)
    # G49 = (((100 - (G48 * C48 / 100)) / 100) * v_mt_node) / (v_nom_mt / v_nom_bt)
    ratio = inp.v_nominal_mt / inp.v_nominal_bt
    v_bt_start = (v_mt_node * (1.0 - (inp.drop_trafo_pct * inp.coef_perda / 10000.0))) / ratio
    
    # 4. BT Segment 1 Drop (H49 pattern)
    v_bt_node1 = v_bt_start * (1.0 - (inp.drop_bt1_pct * inp.coef_perda / 10000.0))
    
    # 5. BT Segment 2 Drop (I49 pattern)
    v_bt_node2 = v_bt_node1 * (1.0 - (inp.drop_bt2_pct * inp.coef_perda / 10000.0))
    
    # 6. Total percentage drop (on BT side)
    v_bt_ideal = inp.v_nominal_bt
    drop_total_pct = ((v_bt_ideal - v_bt_node2) / v_bt_ideal) * 100.0
    
    return QDTResult(
        v_mt_initial=v_mt_initial,
        v_mt_node=v_mt_node,
        v_bt_start=v_bt_start,
        v_bt_node1=v_bt_node1,
        v_bt_node2=v_bt_node2,
        drop_total_pct=drop_total_pct
    )
