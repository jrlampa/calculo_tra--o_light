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
    
    def find_cell_val(ws, keyword, col=None):
        for r in range(1, 100):
            # Scan columns A, B, C, D, G, H, J, K (1, 2, 3, 4, 7, 8, 10, 11)
            for c in [1, 2, 3, 4, 7, 8, 10, 11]:
                if col and c != col: continue
                val = str(ws.cell(row=r, column=c).value or "").upper()
                if keyword.upper() in val:
                    # Return next cell value
                    target_c = c + 1
                    # Check for merged cells or specific layouts
                    res = ws.cell(row=r, column=target_c).value
                    if res is None and target_c < 15:
                        res = ws.cell(row=r, column=target_c+1).value
                    return res
        return None

    ponto = find_cell_val(ws, "Ponto:") or ws["C6"].value
    projeto = find_cell_val(ws, "Projeto:") or ws["C5"].value
    tipo_poste = find_cell_val(ws, "Tipo do Poste") or ws["C140"].value
    modelo_poste = find_cell_val(ws, "Modelo do Poste") or ws["B12"].value

    # Find row anchors for levels
    rede_mt1 = find_row_by_keyword(ws, "MT - 1", col=2) + 7 # T1 rede row is 7 rows below "MT - 1º NÍVEL"
    # Fallback to fixed if anchor fails? No, let's try to be robust. 
    # Usually "MT - 1º NÍVEL" is row 12. Rede is row 19. 19-12 = 7.
    
    # Let's search for "Tipo de rede" explicitly below the anchor
    def find_sub_anchor(ws, start_row, keyword):
        for r in range(start_row, start_row + 15):
             val = str(ws.cell(row=r, column=2).value or "").upper()
             if keyword.upper() in val:
                 return r
        return start_row + 7 # Default offset

    mt1_header = find_row_by_keyword(ws, "MT - 1", col=2)
    rede_mt1 = find_sub_anchor(ws, mt1_header, "Tipo de rede") if mt1_header > 0 else 19

    mt2_header = find_row_by_keyword(ws, "MT - 2", col=2)
    rede_mt2 = find_sub_anchor(ws, mt2_header, "Tipo de rede") if mt2_header > 0 else 45

    bt_header = find_row_by_keyword(ws, "BT", col=2)
    # Search for "BT" header (usually row 64)
    # Avoid picking up "BTZero" or "RAMAIS BTZERO"
    if bt_header > 0:
        val = str(ws.cell(row=bt_header, column=2).value or "").upper()
        if "BTZERO" in val:
             # Look further
             for r in range(bt_header + 1, 200):
                  v = str(ws.cell(row=r, column=2).value or "").upper()
                  if "BT" == v or "BT " in v or "BT" in v:
                      bt_header = r
                      break
    rede_bt = find_sub_anchor(ws, bt_header, "Tipo de rede") if bt_header > 0 else 71

    # 1. Cabecalho
    cab_data = CabecalhoIn(
        projeto=str(projeto or ""),
        ponto=str(ponto or ""),
        endereco=str(ws["C7"].value or ""),
        estudado_por=str(ws["C8"].value or ""),
        data=str(ws["C10"].value or "")
    )
    
    # 2. Poste
    poste_data = PosteIn(
        tipo_poste=str(tipo_poste or ""),
        modelo_poste=str(modelo_poste or "")
    )
    
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
