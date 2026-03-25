import openpyxl
import os

file_path = "AP COSMO LDA NOVA 03 - PROJETO 5 - POSTE 1D.xlsm"
output_file = "cables_excel_dump.txt"

if not os.path.exists(file_path):
    print(f"Arquivo não encontrado: {file_path}")
    exit(1)

wb = openpyxl.load_workbook(file_path, data_only=True)

# Usually cables are in "Plan4" or "Plan1". 
# Let's extract from everywhere potential candidates.
cables = set()

if "Plan4" in wb.sheetnames:
    p4 = wb["Plan4"]
    # Look at column B and C for cable names
    for row in p4.iter_rows(min_row=1, max_row=200, min_col=1, max_col=5):
        for cell in row:
            val = str(cell.value).strip() if cell.value else ""
            if any(key in val for key in ["AWG", "MCM", "mm²", "MTX", "Nu", "XLPE", "PVC"]):
                cables.add(val)

if "Plan1" in wb.sheetnames:
    p1 = wb["Plan1"]
    for row in p1.iter_rows(min_row=1, max_row=100, min_col=1, max_col=10):
        for cell in row:
            val = str(cell.value).strip() if cell.value else ""
            if any(key in val for key in ["AWG", "MCM", "mm²", "MTX", "Nu", "XLPE", "PVC"]):
                cables.add(val)

with open(output_file, "w", encoding="utf-8") as f:
    for c in sorted(list(cables)):
        f.write(c + "\n")

print(f"Total de possíveis condutores encontrados: {len(cables)}")
print(f"Salvo em {output_file}")
