"""Workbook formula and data inventory extractor.

Reads the XLSM workbook without evaluating values (data_only=False) and
produces JSON artifacts under artifacts/ with full traceability:
  - inventory.json   : every formula cell with metadata
  - lookup_tables.json: evaluated Plan1/Plan4 lookup tables (data_only=True)
  - defined_names.json: all 77 defined names categorised
  - manifest.json    : extraction metadata / checksums

Run from the workspace root:
    python python/extract/workbook_inventory.py
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

WORKBOOK_PATH = Path(
    r"AP COSMO LDA NOVA 03 - PROJETO 5 - POSTE 1D.xlsm"
)
ARTIFACTS_DIR = Path(__file__).parent / "artifacts"

# ---------------------------------------------------------------------------
# XML namespaces used inside the OOXML zip
# ---------------------------------------------------------------------------
NS = {
    "ss": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r":  "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
}

FUNC_RE = re.compile(r"(?<![A-Z0-9_\.'])([A-Z][A-Z0-9\._]{1,})\s*\(")


# ---------------------------------------------------------------------------
# Helper: expand shared formulas to per-cell entries
# ---------------------------------------------------------------------------
def _col_num(col_letters: str) -> int:
    n = 0
    for ch in col_letters.upper():
        n = n * 26 + (ord(ch) - ord("A") + 1)
    return n


def _parse_addr(cell_ref: str):
    """Return (col_letter, row_int)."""
    m = re.match(r"([A-Z]+)(\d+)", cell_ref.upper())
    if not m:
        return None, None
    return m.group(1), int(m.group(2))


def _offset_formula(formula: str, col_delta: int, row_delta: int) -> str:
    """Naive A1-reference offset for shared formulas (excludes $ locked refs)."""
    def shift(m: re.Match) -> str:
        col_lock = m.group(1)
        col_txt = m.group(2)
        row_lock = m.group(3)
        row_txt = m.group(4)
        new_col = col_txt
        new_row = row_txt
        if not col_lock:
            n = _col_num(col_txt) + col_delta
            # convert back to letters
            letters = ""
            while n > 0:
                n, r = divmod(n - 1, 26)
                letters = chr(ord("A") + r) + letters
            new_col = letters
        if not row_lock:
            new_row = str(int(row_txt) + row_delta)
        return f"{col_lock}{new_col}{row_lock}{new_row}"

    return re.sub(r"(\$?)([A-Z]+)(\$?)(\d+)", shift, formula)


# ---------------------------------------------------------------------------
# Main extraction
# ---------------------------------------------------------------------------
def extract_inventory(wb_path: Path) -> dict:
    data = {
        "workbook": str(wb_path),
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "sheets": [],
        "defined_names": [],
        "has_vba_project": False,
    }

    with zipfile.ZipFile(wb_path, "r") as z:
        all_names = set(z.namelist())
        data["has_vba_project"] = "xl/vbaProject.bin" in all_names

        wb_xml = ET.fromstring(z.read("xl/workbook.xml"))
        rels_xml = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))

        rel_map: dict[str, str] = {}
        for rel in rels_xml.findall("pr:Relationship", NS):
            rid = rel.get("Id")
            target = rel.get("Target", "")
            if not target.startswith("/"):
                target = "xl/" + target
            rel_map[rid] = target

        # Sheet list
        for s in wb_xml.findall("ss:sheets/ss:sheet", NS):
            name = s.get("name")
            rid = s.get("{%s}id" % NS["r"])
            path = rel_map.get(rid, "")
            sheet_entry = {
                "name": name,
                "sheetId": s.get("sheetId"),
                "path": path,
                "formula_cells": [],
                "formula_count": 0,
            }

            if path not in all_names:
                data["sheets"].append(sheet_entry)
                continue

            sx = ET.fromstring(z.read(path))

            # Shared-formula registry by si index
            shared_master: dict[str, dict] = {}  # si -> {ref, formula}

            func_counter: dict[str, int] = defaultdict(int)

            for c in sx.findall(".//ss:c", NS):
                f_el = c.find("ss:f", NS)
                if f_el is None:
                    continue

                addr = c.get("r", "")
                col_letters, row_num = _parse_addr(addr)
                f_type = f_el.get("t", "")
                si = f_el.get("si")
                f_text = (f_el.text or "").strip()

                # Resolve shared formulas
                if f_type == "shared":
                    if f_text:
                        # This is the MASTER of the shared formula
                        shared_master[si] = {
                            "ref": f_el.get("ref", addr),
                            "formula": f_text,
                            "master_addr": addr,
                            "master_col": col_letters,
                            "master_row": row_num,
                        }
                        resolved_formula = f_text
                    else:
                        # Dependent cell: offset from master
                        master = shared_master.get(si)
                        if master and col_letters and row_num:
                            cd = _col_num(col_letters) - _col_num(master["master_col"])
                            rd = row_num - master["master_row"]
                            resolved_formula = _offset_formula(
                                master["formula"], cd, rd
                            )
                        else:
                            resolved_formula = ""
                else:
                    resolved_formula = f_text

                if not resolved_formula:
                    continue

                upper_f = resolved_formula.upper()
                for m in FUNC_RE.finditer(upper_f):
                    fn = m.group(1)
                    # Exclude obvious false positives (short names that are likely
                    # sheet refs contained in single-quoted names have been handled
                    # because the regex requires 2+ chars)
                    func_counter[fn] += 1

                sheet_entry["formula_cells"].append(
                    {
                        "cell": addr,
                        "formula": resolved_formula,
                        "row": row_num,
                        "col": col_letters,
                        "shared_type": f_type if f_type else "normal",
                        "shared_si": si,
                    }
                )

            sheet_entry["formula_count"] = len(sheet_entry["formula_cells"])
            sheet_entry["functions_used"] = sorted(func_counter.keys())
            sheet_entry["function_counts"] = dict(func_counter)
            data["sheets"].append(sheet_entry)

        # Defined names
        dn_parent = wb_xml.find("ss:definedNames", NS)
        if dn_parent is not None:
            for dn in dn_parent.findall("ss:definedName", NS):
                name = dn.get("name", "")
                local_sheet_id = dn.get("localSheetId")
                expr = (dn.text or "").strip()
                lo = name.lower()
                if lo.startswith("_xlnm."):
                    category = "xlnm"
                elif lo.startswith("solver_"):
                    category = "solver"
                elif lo.startswith("coin_"):
                    category = "coin"
                else:
                    category = "business"
                data["defined_names"].append(
                    {
                        "name": name,
                        "category": category,
                        "local_sheet_id": local_sheet_id,
                        "formula": expr,
                    }
                )

    return data


def extract_lookup_tables(wb_path: Path) -> dict:
    """Read Plan1 and Plan4 with evaluated values for lookup tables."""
    try:
        from openpyxl import load_workbook  # type: ignore
    except ImportError:
        return {"error": "openpyxl not installed"}

    wb = load_workbook(str(wb_path), data_only=True, keep_vba=True)
    tables: dict[str, object] = {}

    # ── Plan1 ──────────────────────────────────────────────
    ws1 = wb["Plan1"]

    # C3:E34 – cable properties (cols 3,4,5 = C,D,E)
    cabos = []
    for r in range(3, 51):
        name_cell = ws1.cell(r, 3).value
        diam_cell = ws1.cell(r, 4).value
        peso_cell = ws1.cell(r, 5).value
        if name_cell is not None:
            cabos.append(
                {
                    "plan1_row": r,
                    "name": name_cell,
                    "diam_m": round(float(diam_cell), 10) if diam_cell is not None else None,
                    "peso_kgm": round(float(peso_cell), 10) if peso_cell is not None else None,
                }
            )

    # N1:O8 – tipo de rede → qtd_cabos (cols 14,15)
    rede = []
    for r in range(1, 9):
        tipo = ws1.cell(r, 14).value
        qtd = ws1.cell(r, 15).value
        if tipo is not None and str(tipo).strip():
            rede.append({"plan1_row": r, "tipo_rede": str(tipo).strip(), "qtd_cabos": qtd})

    # Plan1 row 22: cordoalha (Compacta mensageiro)
    cordoalha = {
        "peso_kgm": ws1.cell(22, 5).value,  # E22
        "diam_m": ws1.cell(22, 4).value,    # D22
        "tipo_rede_trigger": "Compacta",
    }

    # Plan1 J35:L40 – BTZero conductor count table (cols 10,11,12)
    btzero_table = []
    for r in range(35, 41):
        btzero_table.append(
            {
                "plan1_row": r,
                "min_ligacoes": ws1.cell(r, 10).value,
                "max_ligacoes": ws1.cell(r, 11).value,
                "qtd_fios": ws1.cell(r, 12).value,
            }
        )

    # Plan1 C57:E77 – poste type × model → eccentricity force
    poste_table = {}
    current_type = None
    for r in range(57, 78):
        tipo = ws1.cell(r, 3).value
        modelo = ws1.cell(r, 4).value
        force = ws1.cell(r, 5).value
        if tipo is not None:
            current_type = str(tipo).strip()
            if current_type not in poste_table:
                poste_table[current_type] = []
        if modelo is not None and force is not None and current_type:
            poste_table[current_type].append(
                {"plan1_row": r, "modelo": str(modelo).strip(), "forca_ecc_daN": float(force)}
            )

    tables["plan1"] = {
        "cabos_C3E50": cabos,
        "rede_N1O8": rede,
        "cordoalha_row22": cordoalha,
        "btzero_J35L40": btzero_table,
        "poste_C57E77": poste_table,
    }

    # ── Plan4 ──────────────────────────────────────────────
    ws4 = wb["Plan4"]

    # Rows 1–12: cable-type lists by rede category (MT)
    # Row 1 headers: 'Compacta', 'Convencional', 'Multiplexado'
    mt_rede_headers = [ws4.cell(1, c).value for c in range(1, 4)]
    mt_cables: dict[str, list[str]] = {}
    for ci, rh in enumerate(mt_rede_headers, start=1):
        if rh:
            cables = []
            for r in range(2, 13):
                v = ws4.cell(r, ci).value
                if v:
                    cables.append(str(v).strip())
            mt_cables[str(rh).strip()] = cables

    # Row 13 headers: 'Multiplexada', 'Aberta ', 'Armado'
    bt_rede_headers = [ws4.cell(13, c).value for c in range(1, 4)]
    bt_cables: dict[str, list[str]] = {}
    for ci, rh in enumerate(bt_rede_headers, start=1):
        if rh:
            cables = []
            for r in range(14, 20):
                v = ws4.cell(r, ci).value
                if v:
                    cables.append(str(v).strip())
            bt_cables[str(rh).strip()] = cables

    # Row 20 headers: poste type columns
    poste_headers = [ws4.cell(20, c).value for c in range(1, 5)]
    poste_models: dict[str, list[str]] = {}
    for ci, ph in enumerate(poste_headers, start=1):
        if ph:
            models = []
            for r in range(21, 34):
                v = ws4.cell(r, ci).value
                if v:
                    models.append(str(v).strip())
            poste_models[str(ph).strip()] = models

    tables["plan4"] = {
        "mt_cabos_by_rede": mt_cables,
        "bt_cabos_by_rede": bt_cables,
        "poste_models_by_type": poste_models,
    }

    return tables


def main() -> None:
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    if not WORKBOOK_PATH.exists():
        raise FileNotFoundError(f"Workbook not found: {WORKBOOK_PATH}")

    # Checksum
    sha256 = hashlib.sha256(WORKBOOK_PATH.read_bytes()).hexdigest()

    print("Extracting formula inventory …")
    inventory = extract_inventory(WORKBOOK_PATH)

    print("Extracting lookup tables …")
    tables = extract_lookup_tables(WORKBOOK_PATH)

    # Split defined names by category
    defined = inventory.pop("defined_names")
    by_cat: dict[str, list] = defaultdict(list)
    for dn in defined:
        by_cat[dn["category"]].append(dn)

    # Write artifacts
    _write(ARTIFACTS_DIR / "inventory.json", inventory)
    _write(ARTIFACTS_DIR / "lookup_tables.json", tables)
    _write(ARTIFACTS_DIR / "defined_names.json", dict(by_cat))

    # Manifest
    manifest = {
        "workbook_sha256": sha256,
        "workbook_path": str(WORKBOOK_PATH.resolve()),
        "extracted_at": inventory["extracted_at"],
        "sheet_count": len(inventory["sheets"]),
        "formula_counts": {s["name"]: s["formula_count"] for s in inventory["sheets"]},
        "defined_name_count": len(defined),
        "defined_name_categories": {k: len(v) for k, v in by_cat.items()},
        "artifacts": [
            "inventory.json",
            "lookup_tables.json",
            "defined_names.json",
            "manifest.json",
        ],
    }
    _write(ARTIFACTS_DIR / "manifest.json", manifest)

    print(f"\n✓ Artifacts written to {ARTIFACTS_DIR}/")
    for s in inventory["sheets"]:
        print(f"  [{s['name']}] formulas={s['formula_count']}")
    print(
        f"  Defined names: {len(defined)} "
        f"(business={len(by_cat['business'])}, "
        f"solver={len(by_cat['solver'])}, "
        f"coin={len(by_cat['coin'])}, "
        f"xlnm={len(by_cat['xlnm'])})"
    )
    print(f"  Workbook SHA-256: {sha256[:16]}…")


def _write(path: Path, data: object) -> None:
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )
    print(f"  → {path.name}")


if __name__ == "__main__":
    main()
