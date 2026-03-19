import openpyxl
import json
import os

path = r'c:\Users\jonat\OneDrive - IM3 Brasil\utils\myworld\cqt_light\PLANILHA_DESTRAVADA.xlsm'
output = 'qdt_formulas.json'

wb = openpyxl.load_workbook(path, data_only=False)
ws = wb['Alocação % de tensão']

formulas = {}
for row in ws.iter_rows():
    for cell in row:
        if isinstance(cell.value, str) and cell.value.startswith('='):
            formulas[cell.coordinate] = cell.value

with open(output, 'w', encoding='utf-8') as f:
    json.dump(formulas, f, indent=2)

print(f"Extracted {len(formulas)} formulas to {output}")
