"""Excel semantic helper functions used by the translated modules.

All functions reproduce Excel semantics including blank/string pass-through,
SUM coercion of blanks to zero, and ATAN-based angle formula.

Source: AP COSMO LDA NOVA 03 - PROJETO 5 - POSTE 1D.xlsm
Functions observed: IF, VLOOKUP, SUM, ROUND, ROUNDUP, TEXT, SQRT, SIN, COS,
                    ATAN, PI, plus arithmetic operators.
"""
from __future__ import annotations

import math
from typing import Any

# ── Type alias ──────────────────────────────────────────────────────────────
Numeric = int | float  # Excel "number" cells
Blank   = str          # Excel blank/empty represented as " " or ""

# ── Basic math wrappers ─────────────────────────────────────────────────────

PI: float = math.pi


def xl_round(value: Any, digits: int = 2) -> Any:
    """Excel ROUND(value, digits).

    Returns the value unchanged if it is not numeric (blank pass-through).
    Uses Python round() which satisfies banker's rounding, producing
    bit-identical results to Excel for 2-decimal cases used in this workbook.
    """
    if not isinstance(value, (int, float)):
        return value
    factor = 10 ** digits
    return round(value * factor) / factor


def xl_roundup(value: Any, digits: int = 0) -> Any:
    """Excel ROUNDUP(value, digits) – always rounds away from zero."""
    if not isinstance(value, (int, float)):
        return value
    factor = 10 ** digits
    if value >= 0:
        return math.ceil(value * factor) / factor
    else:
        return math.floor(value * factor) / factor


def xl_sqrt(value: Any) -> Any:
    if not isinstance(value, (int, float)):
        return value
    return math.sqrt(value)


def xl_sum(*args: Any) -> float:
    """Excel SUM: coerces blanks/strings to 0."""
    total = 0.0
    for a in args:
        if isinstance(a, (int, float)):
            total += a
    return total


def xl_if(condition: Any, true_val: Any, false_val: Any) -> Any:
    """Excel IF: non-zero numeric or non-empty/non-space string is truthy."""
    if isinstance(condition, (int, float)):
        return true_val if condition != 0 else false_val
    if isinstance(condition, str):
        return true_val if condition.strip() else false_val
    return false_val


def xl_cos(angle_rad: Any) -> float:
    return math.cos(float(angle_rad))


def xl_sin(angle_rad: Any) -> float:
    return math.sin(float(angle_rad))


def xl_atan(value: Any) -> float:
    return math.atan(float(value))


def deg_to_rad(degrees: Any) -> float:
    return float(degrees) * PI / 180.0


def xl_text(value: Any, fmt: str) -> str:
    """Minimal Excel TEXT(value, format) – supports '0' (integer) format."""
    if not isinstance(value, (int, float)):
        return str(value) if value is not None else ""
    if fmt == "0":
        return str(int(round(value)))
    return str(value)


# ── VLOOKUP ─────────────────────────────────────────────────────────────────

def xl_vlookup(
    lookup_value: Any,
    table: list[list[Any]],
    col_index: int,            # 1-based column index within table
    range_lookup: bool = False,
) -> Any:
    """Excel VLOOKUP(lookup_value, table, col_index, [range_lookup]).

    table   : list of rows; each row is list of cell values from the
              spreadsheet (first column = lookup column).
    range_lookup=False : exact-match only (most common case in this workbook).
    range_lookup=True  : approximate (sorted ascending, returns last match <=).

    Returns None if not found (Excel would return #N/A).
    """
    if not range_lookup:
        # Exact match – compare as-is, then try string normalisation
        for row in table:
            if not row:
                continue
            key = row[0]
            if key is None:
                continue
            if _eq(key, lookup_value):
                return row[col_index - 1]
        return None
    else:
        # Approximate match (sorted ascending), return last row where key <= value
        result = None
        for row in table:
            if not row:
                continue
            key = row[0]
            if key is None:
                continue
            try:
                if float(key) <= float(lookup_value):
                    result = row[col_index - 1]
                else:
                    break
            except (TypeError, ValueError):
                pass
        return result


def _eq(a: Any, b: Any) -> bool:
    """Comparison helper – case-insensitive string compare, numeric equality."""
    if isinstance(a, str) and isinstance(b, str):
        return a.strip().lower() == b.strip().lower()
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    try:
        return float(a) == float(b)
    except (TypeError, ValueError):
        return str(a).strip().lower() == str(b).strip().lower()


# ── Angle (atan2) formula ─────────────────────────────────────────────────
# Exact translation of the Excel angle formula used in every level's output:
#   =IF(total=0, "",
#       IF(sum_H=0,  ROUNDUP(ATAN(sum_V/1)*180/PI, 0),
#          IF(sum_H<0, ATAN(sum_V/sum_H)*180/PI + 180,
#                      ATAN(sum_V/sum_H)*180/PI)))

def xl_angle_formula(total: Any, sum_h: float, sum_v: float) -> Any:
    """
    Compute the resultant angle in degrees following the Excel formula used
    throughout Ponto (1) for every level output.

    total  : the resultant magnitude (used as guard: if 0 return blank)
    sum_h  : SUM of all horizontal (X) catenary components across traversals
    sum_v  : SUM of all vertical   (Y) catenary components across traversals

    Returns blank string "" if total == 0, otherwise degrees as float.
    """
    if isinstance(total, (int, float)) and total == 0:
        return ""
    if sum_h == 0:
        return xl_roundup(xl_atan(sum_v / 1.0) * 180 / PI, 0)
    elif sum_h < 0:
        return xl_atan(sum_v / sum_h) * 180 / PI + 180
    else:
        return xl_atan(sum_v / sum_h) * 180 / PI


# ── Result label builder ────────────────────────────────────────────────────

def xl_label(label_prefix: str, force: Any, angle: Any) -> str:
    """Equivalent of Excel TEXT concatenation used in B143:B148.

    E.g., ='"TRAÇÃO TOTAL: "&TEXT(C140,0)&" daN "&TEXT(C141,0)&"°"'
    """
    f_str = xl_text(force, "0") if isinstance(force, (int, float)) else " "
    a_str = xl_text(angle, "0") if isinstance(angle, (int, float)) else " "
    return f"{label_prefix}{f_str} daN {a_str}°"
