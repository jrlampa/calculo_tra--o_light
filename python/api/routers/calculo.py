"""Router para endpoints de cálculo de tração.

Thin router: validates input via Pydantic, delegates computation to the
service layer, and returns the structured response.  Business logic
(input mapping, domain assembly) lives in ``services.calculo_service``.
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException, UploadFile, File
from services.excel_import import extract_excel_to_input

from api.schemas import (
    CalculoInput,
    CalculoOutput,
    QDTInput,
    QDTOutput,
)
from services.calculo_service import calculo_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calcular", tags=["Cálculo"])


@router.post("/qdt", response_model=QDTOutput)
def calculate_qdt(inp: QDTInput) -> QDTOutput:
    """Run the Voltage Drop (QDT) calculation."""
    return calculo_service.calcular_qdt(inp)


@router.post("/importar-excel", response_model=CalculoInput, tags=["Importação"])
async def importar_excel(file: UploadFile = File(...)) -> CalculoInput:
    """Import legacy Excel data to pre-fill the frontend form."""
    if not file.filename.lower().endswith((".xlsm", ".xlsx")):
        raise HTTPException(status_code=400, detail="Apenas arquivos .xlsm ou .xlsx são permitidos")

    try:
        content = await file.read()
        extracted_data = extract_excel_to_input(content)
        return extracted_data
    except Exception as e:
        logger.exception("Erro ao importar planilha: %s", e)
        raise HTTPException(status_code=500, detail=f"Erro ao processar planilha: {str(e)}")


@router.post("", response_model=CalculoOutput)
def calcular(inp: CalculoInput) -> CalculoOutput:
    """Run the Ponto (1) calculation and return structured results."""
    try:
        return calculo_service.calcular(inp)
    except (ValueError, ZeroDivisionError, ArithmeticError) as domain_err:
        logger.warning("Entrada inválida em /calcular: %s", domain_err)
        raise HTTPException(
            status_code=422,
            detail=f"Entrada fora do domínio operacional: {domain_err}",
        )
    except Exception:
        logger.exception("Erro interno durante /calcular")
        raise HTTPException(status_code=500, detail="Erro interno ao processar cálculo")
