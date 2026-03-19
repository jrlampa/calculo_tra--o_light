import openpyxl
import json

path = r'c:\Users\jonat\OneDrive - IM3 Brasil\utils\myworld\calculo_tração_light\AP COSMO LDA NOVA 03 - PROJETO 5 - POSTE 1D.xlsm'
wb = openpyxl.load_workbook(path, data_only=True)
ws = wb['Plan4']

data = []
for row in ws.iter_rows(min_row=1, max_row=500, values_only=True):
    if any(row):
        data.append(row)

with open('material_plan4_raw.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Extracted {len(data)} rows from Plan4 to material_plan4_raw.json")
