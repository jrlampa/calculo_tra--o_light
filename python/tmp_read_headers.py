import openpyxl

path = r'c:\Users\jonat\OneDrive - IM3 Brasil\utils\myworld\cqt_light\PLANILHA_DESTRAVADA.xlsm'
wb = openpyxl.load_workbook(path, data_only=True)
ws = wb['Alocação % de tensão']

print(f"{'Cell':<6} | {'Value'}")
print("-" * 20)
for row_idx in range(40, 50):
    for col_idx in range(1, 25):
        cell = ws.cell(row=row_idx, column=col_idx)
        if cell.value:
            print(f"{cell.coordinate:<6} | {cell.value}")
