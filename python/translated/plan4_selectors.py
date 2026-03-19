"""Plan4 cable/pole selector helpers translated from named ranges.

Source: AP COSMO LDA NOVA 03 - PROJETO 5 - POSTE 1D.xlsm  →  Plan4
Named ranges: Tipo, Tipo2–Tipo8 (MT), Tipo9–Tipo12 (BT), Poste

Each named range is an OFFSET/MATCH dynamic range returning a column of
allowed values for a given tipo_rede (MT/BT) or tipo_poste (Pole).
These are translated to simple dict-based lookups.

Inventory artifact: python/extract/artifacts/defined_names.json  (business category)
"""
from __future__ import annotations

# ── Plan4 A1:C12 – MT cable lists by rede ──────────────────────────────────
# Plan4 rows 1–12: headers on row 1, cables in rows 2–12
MT_CABOS_BY_REDE: dict[str, list[str]] = {
    "Compacta": [
        "397MCM-CA, XLPE, 34,5 kV",
        "397MCM-CA, XLPE, 13,8 kV",
        "1/0AWG-CAA, XLPE, 13,8 kV",
        "4 AWG-CAA, XLPE, 13,8 kV",
        "185mm², MTX-MT, 20/35 kV",
        "185mm², MTX-MT, 12/20 kV",
        "50mm², MTX-MT, 12/20 kV",
        "397MCM-CA, XLPE, 13,8 kV",
    ],
    "Convencional": [
        "556MCM-CA, Nu",
        "397MCM-CA, Nu",
        "1/0AWG-CAA, Nu",
        "4 AWG-CAA, Nu",
        "397MCM-CA, XLPE, 34,5 kV",
        "397MCM-CA, XLPE, 13,8 kV",
        "1/0AWG-CAA, XLPE, 13,8 kV",
        "4 AWG-CAA, XLPE, 13,8 kV",
    ],
    "Multiplexado": [
        "185mm², MTX-MT, 20/35 kV",
        "185mm², MTX-MT, 12/20 kV",
        "50mm², MTX-MT, 12/20 kV",
    ],
}

# ── Plan4 A13:C16 – BT cable lists by rede ─────────────────────────────────
BT_CABOS_BY_REDE: dict[str, list[str]] = {
    "Multiplexada": [
        "240mm², MTX-BT ",
        "185mm², MTX-BT ",
        "70mm², MTX-BT ",
    ],
    "Aberta ": [
        "397MCM-CA, PVC",
        "1/0AWG-CAA, PVC ",
    ],
    "Armado": [
        "Cabo armado 240mm² ",
        "Cabo armado 95mm² ",
    ],
}

# ── Plan4 A20:D32 – poste models by type ───────────────────────────────────
POSTE_MODELS_BY_TYPE: dict[str, list[str]] = {
    "Concreto circular": [
        "9 m / 150 daN",
        "9 m / 300 daN",
        "11 m / 300 daN",
        "11 m / 600 daN",
        "11 m / 1000 daN",
        "11 m / 1500 daN",
        "12 m / 300 daN",
        "12 m / 600 daN",
        "12 m / 1000 daN",
        "12 m / 200 daN",
        "15 m / 1000 daN",
        "18 m / 1000 daN",
    ],
    "Fibra de vidro circular": [
        "9 m / 300 daN",
        "11 m / 300 daN",
        "11 m / 600 daN",
        "12 m / 600 daN",
    ],
    "Concreto duplo T": [
        "9 m / 300 daN",
        "11 m / 300 daN",
        "11 m / 600 daN",
        "12 m / 600 daN",
    ],
    "Metálico": [
        "7,5 m / 200 daN",
    ],
}


def get_mt_cabos(tipo_rede: str) -> list[str]:
    """Return allowed MT cable types for the given tipo_rede (Plan4 Tipo named range)."""
    return MT_CABOS_BY_REDE.get(tipo_rede.strip(), [])


def get_bt_cabos(tipo_rede: str) -> list[str]:
    """Return allowed BT cable types for the given tipo_rede (Plan4 Tipo9-12 named range)."""
    return BT_CABOS_BY_REDE.get(tipo_rede.strip(), [])


def get_poste_models(tipo_poste: str) -> list[str]:
    """Return allowed models for the given pole type (Plan4 Poste named range)."""
    for key, models in POSTE_MODELS_BY_TYPE.items():
        if key.strip().lower() == tipo_poste.strip().lower():
            return models
    return []
