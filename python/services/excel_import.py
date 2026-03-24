import logging
from io import BytesIO
from typing import Any, Dict, List
import openpyxl
from api.schemas import (
    CalculoInput, 
    MTTraversalIn, 
    BTTraversalIn, 
    BTZeroTraversalIn, 
    RamaisTraversalIn,
    PosteIn,
    CabecalhoIn
)

logger = logging.getLogger(__name__)

def safe_float(value: Any) -> float:
    """Safe conversion from Excel cell to float."""
    try:
        if value is None or str(value).strip() == "":
            return 0.0
        if isinstance(value, str):
            return float(value.replace(",", "."))
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def find_row_by_keyword(ws, keyword: str, start_row: int = 1, col: int = 1) -> int:
    """Find row index containing keyword in specific column."""
    for row in range(start_row, min(ws.max_row, 300)):
        val = str(ws.cell(row=row, column=col).value or "").strip().upper()
        if keyword in val:
            return row
    return -1

def extract_excel_to_input(file_content: bytes) -> CalculoInput:
    """Extracts engineering data from legacy XLSM/XLSX to CalculoInput schema."""
    wb = openpyxl.load_workbook(BytesIO(file_content), data_only=True)
    ws = wb.active
    
    # Anchors
    total_row = find_row_by_keyword(ws, "TOTAL", 120, 1)
    if total_row == -1: total_row = 142
    
    rede_mt1 = find_row_by_keyword(ws, "REDE", 12, 1)
    if rede_mt1 == -1: rede_mt1 = 19
    
    rede_mt2 = find_row_by_keyword(ws, "REDE", 38, 1)
    if rede_mt2 == -1: rede_mt2 = 45
    
    rede_bt = find_row_by_keyword(ws, "REDE", 64, 1)
    if rede_bt == -1: rede_bt = 71
    
    # 1. Cabecalho
    cab_data = CabecalhoIn(
        projeto=str(ws["C5"].value or ""),
        ponto=str(ws["C6"].value or ""),
        endereco=str(ws["C7"].value or ""),
        estudado_por=str(ws["C8"].value or ""),
        data=str(ws["C10"].value or "")
    )
    
    # 2. Poste
    poste_data = PosteIn(
        tipo_poste=str(ws["C140"].value or ""),
        modelo_poste=str(ws["B12"].value or "")
        # Note: audit script uses B12, but UI has specific selects. 
        # We try to map to what's in B12 string (ex: 'DT 11/600')
    )
    if "DT" in poste_data.modelo_poste.upper():
        poste_data.tipo_poste = "Concreto Duplo T"
    elif "CIRC" in poste_data.modelo_poste.upper():
        poste_data.tipo_poste = "Concreto circular"
    
    # 3. Traversals
    def get_mt_row(anchor, col_offset):
        # Col 3=C, 6=F, 9=I, 12=L
        col = 3 + (col_offset * 3)
        return MTTraversalIn(
            tipo_rede=str(ws.cell(row=anchor, column=col).value or ""),
            tipo_cabo=str(ws.cell(row=anchor+1, column=col).value or ""),
            vao=safe_float(ws.cell(row=anchor-5, column=col).value),
            flecha=safe_float(ws.cell(row=anchor-4, column=col).value),
            angulo=safe_float(ws.cell(row=anchor-3, column=col).value),
            altura_poste=safe_float(ws.cell(row=anchor-2, column=col).value),
            altura_ancoragem=safe_float(ws.cell(row=anchor-1, column=col).value),
        )

    mt1 = [get_mt_row(rede_mt1, i) for i in range(4)]
    mt2 = [get_mt_row(rede_mt2, i) for i in range(4)]
    
    # BT special geometry
    bt = []
    for i in range(4):
        col = 3 + (i * 3)
        bt.append(BTTraversalIn(
            tipo_rede=str(ws.cell(row=rede_bt, column=col).value or ""),
            tipo_cabo=str(ws.cell(row=rede_bt+1, column=col).value or ""),
            altura_ancoragem=safe_float(ws.cell(row=rede_bt-1, column=col).value),
            # Geometry for BT is inherited from MT1 in many cases, but we fill it here too
            vao=safe_float(ws.cell(row=rede_bt-5, column=col).value),
            flecha=safe_float(ws.cell(row=rede_bt-4, column=col).value),
            angulo=safe_float(ws.cell(row=rede_bt-3, column=col).value),
            altura_poste=safe_float(ws.cell(row=rede_bt-2, column=col).value),
        ))

    # BTZero and Ramais are often empty in legacy or hard to find in a fixed row.
    # We default them as empty for now or try to find anchors if they exist.
    btz = [BTZeroTraversalIn() for _ in range(4)]
    ral = [RamaisTraversalIn() for _ in range(4)]
    
    return CalculoInput(
        cabecalho=cab_data,
        poste=poste_data,
        mt1=mt1,
        mt2=mt2,
        bt=bt,
        btz=btz,
        ral=ral
    )
