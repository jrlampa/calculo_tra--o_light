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

def find_row_by_keyword(ws, keyword: str, start_row: int = 1, col_range: List[int] = [1, 2]) -> int:
    """Find row index containing keyword in specified columns."""
    for row in range(start_row, min(ws.max_row, 350)):
        for c in col_range:
            val = str(ws.cell(row=row, column=c).value or "").strip().upper()
            # Be very strict with level headers to avoid picking up partial matches
            if keyword.upper() == "MT - 1" or keyword.upper() == "MT - 1º NÍVEL":
                if "MT - 1" in val: return row
            elif keyword.upper() == "BT":
                # Strict BT to avoid BTZERO or RAMAIS BTZERO
                if val == "BT" or val == "BT:": return row
            elif keyword.upper() in val:
                return row
    return -1

def extract_excel_to_input(file_content: bytes) -> CalculoInput:
    """Extracts engineering data from legacy XLSM/XLSX to CalculoInput schema."""
    wb = openpyxl.load_workbook(BytesIO(file_content), data_only=True)
    ws = wb.active
    
    # Find row anchors for levels using multi-column scan
    # Increase col_range to 1-4 just in case
    mt1_header = find_row_by_keyword(ws, "MT - 1", col_range=[1, 2, 3, 4])
    
    def find_sub_anchor_multi(ws, start_row, keyword, col_range=[1, 2, 3]):
        if start_row <= 0: return -1
        # Search up to 25 rows below header for "Tipo de rede"
        for r in range(start_row, start_row + 25):
             for c in col_range:
                 val = str(ws.cell(row=r, column=c).value or "").upper()
                 if keyword.upper() in val:
                     return r
        return start_row + 7

    rede_mt1 = find_sub_anchor_multi(ws, mt1_header, "Tipo de rede") if mt1_header > 0 else 19

    mt2_header = find_row_by_keyword(ws, "MT - 2", col_range=[1, 2, 3, 4])
    rede_mt2 = find_sub_anchor_multi(ws, mt2_header, "Tipo de rede") if mt2_header > 0 else 45

    bt_header = find_row_by_keyword(ws, "BT", col_range=[1, 2, 3, 4])
    # Distinguish BT from BTZERO
    rede_bt = find_sub_anchor_multi(ws, bt_header, "Tipo de rede") if bt_header > 0 else 71

    # 1. Cabecalho logic improvement
    def find_field_val_flexible(ws, keyword, start_row=1, end_row=50):
        # Scan Column A to F for the keyword
        for r in range(start_row, end_row):
             for c in range(1, 8):
                  val = str(ws.cell(row=r, column=c).value or "").strip().upper()
                  if keyword.upper() in val:
                       # The value is usually the next cell
                       return ws.cell(row=r, column=c+1).value
        return None

    projeto = find_field_val_flexible(ws, "Projeto:") or ws["C5"].value
    ponto = find_field_val_flexible(ws, "Ponto:") or ws["C6"].value
    # Endereco, Maria, Data
    endereco = find_field_val_flexible(ws, "Endereço:") or ws["C7"].value
    estudado_por = find_field_val_flexible(ws, "Estudado por:") or ws["C8"].value
    data_val = find_field_val_flexible(ws, "Data:") or ws["C10"].value

    cab_data = CabecalhoIn(
        projeto=str(projeto or ""),
        ponto=str(ponto or ""),
        endereco=str(endereco or ""),
        estudado_por=str(estudado_por or ""),
        data=str(data_val or "")
    )
    
    # 2. Poste
    tipo_poste_val = find_field_val_flexible(ws, "Tipo do Poste") or ws["C140"].value
    modelo_poste_val = find_field_val_flexible(ws, "Modelo do Poste") or ws["B12"].value
    
    poste_data = PosteIn(
        tipo_poste=str(tipo_poste_val or ""),
        modelo_poste=str(modelo_poste_val or "")
    )
    
    # 3. Traversals cols - use robust fallback [2, 5, 8, 11] if T1 not found
    def get_traversal_cols(ws, header_row):
        cols = []
        if header_row > 0:
            for r in range(header_row, header_row + 15):
                for c in range(1, 15):
                    v = str(ws.cell(row=r, column=c).value or "").strip().upper()
                    if v in ["T1", "T2", "T3", "T4"]:
                        cols.append(c)
                if len(cols) >= 4: break
        
        if len(cols) < 4:
            # Fallback to standard columns (B, E, H, K)
            return [2, 5, 8, 11]
        return sorted(list(set(cols)))[:4]

    mt1_cols = get_traversal_cols(ws, mt1_header)
    mt2_cols = get_traversal_cols(ws, mt2_header)
    bt_cols  = get_traversal_cols(ws, bt_header)

    def get_mt_row_dyn(anchor, cols, i):
        col = cols[i]
        return MTTraversalIn(
            tipo_rede=str(ws.cell(row=anchor, column=col).value or ""),
            tipo_cabo=str(ws.cell(row=anchor+1, column=col).value or ""),
            vao=safe_float(ws.cell(row=anchor-5, column=col).value),
            flecha=safe_float(ws.cell(row=anchor-4, column=col).value),
            angulo=safe_float(ws.cell(row=anchor-3, column=col).value),
            altura_poste=safe_float(ws.cell(row=anchor-2, column=col).value),
            altura_ancoragem=safe_float(ws.cell(row=anchor-1, column=col).value),
        )

    mt1 = [get_mt_row_dyn(rede_mt1, mt1_cols, i) for i in range(4)]
    mt2 = [get_mt_row_dyn(rede_mt2, mt2_cols, i) for i in range(4)]
    
    # BT special geometry
    bt = []
    for i in range(4):
        col = bt_cols[i]
        bt.append(BTTraversalIn(
            tipo_rede=str(ws.cell(row=rede_bt, column=col).value or ""),
            tipo_cabo=str(ws.cell(row=rede_bt+1, column=col).value or ""),
            altura_ancoragem=safe_float(ws.cell(row=rede_bt-1, column=col).value),
            vao=safe_float(ws.cell(row=rede_bt-5, column=col).value),
            flecha=safe_float(ws.cell(row=rede_bt-4, column=col).value),
            angulo=safe_float(ws.cell(row=rede_bt-3, column=col).value),
            altura_poste=safe_float(ws.cell(row=rede_bt-2, column=col).value),
        ))

    # BTZero and Ramais
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
