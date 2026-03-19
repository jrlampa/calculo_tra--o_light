"""solver_coin.py – Solver and COIN defined-name metadata.

Encodes the 57 solver_* and 6 coin_* names as a Python dict with
provenance information (source sheet, formula/value).

These names are used by the Excel Solver add-in and are NOT part of the
engineering calculation.  They are included here for completeness and
round-trip serialisation of the workbook's defined-name namespace.

Source: python/extract/artifacts/defined_names.json  category=solver / coin
"""
from __future__ import annotations

# ── Solver parameters ──────────────────────────────────────────────────────
# Each entry: { "value": <formula_or_constant>, "scope": <sheet|workbook> }

SOLVER_NAMES: dict[str, dict] = {
    "solver_adj":     {"value": "\"$C$12\"",              "scope": "workbook"},
    "solver_cvg":     {"value": "0.001",                  "scope": "workbook"},
    "solver_drv":     {"value": "1",                      "scope": "workbook"},
    "solver_eng":     {"value": "1",                      "scope": "workbook"},
    "solver_fct":     {"value": "0.16",                   "scope": "workbook"},
    "solver_grb":     {"value": "\"\"",                   "scope": "workbook"},
    "solver_int":     {"value": "5",                      "scope": "workbook"},
    "solver_itr":     {"value": "100",                    "scope": "workbook"},
    "solver_lim":     {"value": "\"\"",                   "scope": "workbook"},
    "solver_lod":     {"value": "0",                      "scope": "workbook"},
    "solver_met":     {"value": "2",                      "scope": "workbook"},
    "solver_mip":     {"value": "0.05",                   "scope": "workbook"},
    "solver_mxi":     {"value": "10000",                  "scope": "workbook"},
    "solver_mxj":     {"value": "10000",                  "scope": "workbook"},
    "solver_mxn":     {"value": "10000",                  "scope": "workbook"},
    "solver_mxt":     {"value": "10000",                  "scope": "workbook"},
    "solver_neg":     {"value": "1",                      "scope": "workbook"},
    "solver_nwt":     {"value": "1",                      "scope": "workbook"},
    "solver_obj":     {"value": "\"\"",                   "scope": "workbook"},
    "solver_oma":     {"value": "\"\"",                   "scope": "workbook"},
    "solver_op":      {"value": "1",                      "scope": "workbook"},
    "solver_piv":     {"value": "\"\"",                   "scope": "workbook"},
    "solver_pla":     {"value": "\"\"",                   "scope": "workbook"},
    "solver_pre":     {"value": "1E-06",                  "scope": "workbook"},
    "solver_rng":     {"value": "\"\"",                   "scope": "workbook"},
    "solver_rol":     {"value": "\"\"",                   "scope": "workbook"},
    "solver_scl":     {"value": "\"FALSE\"",              "scope": "workbook"},
    "solver_sho":     {"value": "0",                      "scope": "workbook"},
    "solver_slf":     {"value": "\"FALSE\"",              "scope": "workbook"},
    "solver_slp":     {"value": "5",                      "scope": "workbook"},
    "solver_sln":     {"value": "0",                      "scope": "workbook"},
    "solver_sta":     {"value": "\"\"",                   "scope": "workbook"},
    "solver_stc":     {"value": "0",                      "scope": "workbook"},
    "solver_stl":     {"value": "\"\"",                   "scope": "workbook"},
    "solver_stn":     {"value": "0",                      "scope": "workbook"},
    "solver_sto":     {"value": "\"\"",                   "scope": "workbook"},
    "solver_sub":     {"value": "\"\"",                   "scope": "workbook"},
    "solver_sum":     {"value": "1",                      "scope": "workbook"},
    "solver_tln":     {"value": "0",                      "scope": "workbook"},
    "solver_tol":     {"value": "5",                      "scope": "workbook"},
    "solver_typ":     {"value": "1",                      "scope": "workbook"},
    "solver_una":     {"value": "\"\"",                   "scope": "workbook"},
    "solver_unl":     {"value": "\"\"",                   "scope": "workbook"},
    "solver_val":     {"value": "\"0\"",                  "scope": "workbook"},
    "solver_ver":     {"value": "\"40\"",                 "scope": "workbook"},
}

# ── COIN (open-source solver) parameters ──────────────────────────────────

COIN_NAMES: dict[str, dict] = {
    "coin_dpts":  {"value": "\"\"",  "scope": "workbook"},
    "coin_log":   {"value": "1",     "scope": "workbook"},
    "coin_mobj":  {"value": "1",     "scope": "workbook"},
    "coin_mprc":  {"value": "1",     "scope": "workbook"},
    "coin_npts":  {"value": "0",     "scope": "workbook"},
    "coin_sobj":  {"value": "0",     "scope": "workbook"},
}

# ── Combined view ──────────────────────────────────────────────────────────

ALL_SOLVER_COIN: dict[str, dict] = {**SOLVER_NAMES, **COIN_NAMES}


def get_solver_param(name: str) -> str | None:
    """Return the value string for a solver/coin parameter, or None if unknown."""
    entry = ALL_SOLVER_COIN.get(name)
    return entry["value"] if entry else None
