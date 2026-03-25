
import openpyxl
import sys

def debug(filepath):
    print(f"DEBUGGING: {filepath}")
    wb = openpyxl.load_workbook(filepath, data_only=True)
    ws = wb['Ponto (1)']
    
    # Dump common areas
    print("--- HEADER (Row 1-5) ---")
    for r in range(1, 6):
        for c in range(1, 15):
            val = ws.cell(row=r, column=c).value
            if val:
                print(f"({r},{c}) [{openpyxl.utils.get_column_letter(c)}{r}]: {val}")
                
    print("\n--- RESULTS AREA (Row 130-150) ---")
    for r in range(130, 150):
        for c in range(1, 10):
            val = ws.cell(row=r, column=c).value
            if val:
                print(f"({r},{c}) [{openpyxl.utils.get_column_letter(c)}{r}]: {val}")

if __name__ == "__main__":
    p = r"C:\Users\jonat\OneDrive - IM3 Brasil\LIGHT\PROJETOS\REDE CLANDESTINA - RUAS JERUSALÉM E UVA - SANTA CRUZ RJ\CALC TRAÇÃO\PROJETO I - RUA JERUSALÉM\CLANDESTINO - RUA JERUSALÉM - PROJETO I - POSTE 1.xlsm"
    debug(p)
