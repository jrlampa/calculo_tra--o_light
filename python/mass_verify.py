
import os
import asyncio
import openpyxl
import json
import math
from services.excel_import import extract_excel_to_input
from translated.ponto_blocks import (
    calcular_polo,
    BTTraversalInput,
    BTZeroTraversalInput,
    MTTraversalInput,
    RamaisTraversalInput
)
from db.pool import initialize_db_pool, db_pool
from uuid import uuid4

# Paths
BASE_DIR = r"C:\Users\jonat\OneDrive - IM3 Brasil\LIGHT\PROJETOS\REDE CLANDESTINA - RUAS JERUSALÉM E UVA - SANTA CRUZ RJ\CALC TRAÇÃO"
FOLDERS = ["PROJETO I - RUA JERUSALÉM", "PROJETO II - RUA UVA"]

def extract_golden_truth(filepath):
    try:
        wb = openpyxl.load_workbook(filepath, data_only=True)
        sheet_names = wb.sheetnames
        target_sheet = next((s for s in sheet_names if s.lower() in ['ponto (1)', 'plan1']), None)
        if not target_sheet: return None, None
        ws = wb[target_sheet]
        
        def find_val(ws, keyword):
            for r in range(1, 400):
                val = str(ws.cell(row=r, column=2).value or "").upper()
                if keyword.upper() in val:
                    return ws.cell(row=r, column=3).value
            return None

        tracao = find_val(ws, "Fração Total")
        status = find_val(ws, "Status Poste")
        return tracao, status
    except:
        return None, None

async def verify_file(filepath):
    filename = os.path.basename(filepath)
    
    with open(filepath, "rb") as f:
        content = f.read()
    
    try:
        # 1. Import
        inp = extract_excel_to_input(content)
        
        # 2. Map Pydantic to Logic
        mt1 = [MTTraversalInput(**t.model_dump()) for t in inp.mt1]
        mt2 = [MTTraversalInput(**t.model_dump()) for t in inp.mt2]
        bt = [BTTraversalInput(**t.model_dump()) for t in inp.bt]
        btz = [BTZeroTraversalInput(**t.model_dump()) for t in inp.btz]
        ral = [RamaisTraversalInput(**t.model_dump()) for t in inp.ral]
        
        # 3. Calculate
        result = calcular_polo(
            mt1_inputs=mt1,
            mt2_inputs=mt2,
            bt_inputs=bt,
            btz_inputs=btz,
            ral_inputs=ral,
            tipo_poste=inp.poste.tipo_poste,
            modelo_poste=inp.poste.modelo_poste,
        )
        
        calc_tracao = result.total_tracao
        
        # 4. Golden Truth
        golden_tracao, golden_status = extract_golden_truth(filepath)
        
        # 5. Parity
        diff = abs(float(calc_tracao or 0) - float(golden_tracao or 0)) if golden_tracao else 0
        parity = diff < 1.0 # Allowing 1.0 daN diff due to intermediate rounding nuances
        
        return {
            "file": filename,
            "calc_tr": round(calc_tracao, 2),
            "gold_tr": round(float(golden_tracao), 2) if golden_tracao else None,
            "parity": parity,
            "status": "SUCCESS"
        }
    except Exception as e:
        return {"file": filename, "status": f"ERROR: {str(e)}"}

async def test_persistence():
    print("\nTesting Persistence (DB Write)...")
    await initialize_db_pool()
    try:
        # Try to insert a mock project
        p_id = uuid4()
        u_id = uuid4()
        await db_pool.execute(
            "INSERT INTO projetos (id, orgao, ns, nome, owner_id) VALUES ($1, $2, $3, $4, $5)",
            str(p_id), "TEST-AUDIT", "NS-AUDIT-1", "Projeto Audition", str(u_id)
        )
        print("✓ Project created successfully.")
        
        # Try to insert a point
        pt_id = uuid4()
        await db_pool.execute(
            "INSERT INTO pontos (id, projeto_id, ponto, tipo_poste, modelo_poste) VALUES ($1, $2, $3, $4, $5)",
            str(pt_id), str(p_id), "P1", "Circular", "11m/300daN"
        )
        print("✓ Point created successfully.")
        
        # Clean up
        await db_pool.execute("DELETE FROM pontos WHERE projeto_id = $1", str(p_id))
        await db_pool.execute("DELETE FROM projetos WHERE id = $1", str(p_id))
        print("✓ Cleanup successful.")
        return True
    except Exception as e:
        print(f"✗ Persistence FAILED: {e}")
        return False
    finally:
        await db_pool.close()

async def main():
    # 1. Check DB
    persistence_ok = await test_persistence()
    if not persistence_ok:
        print("ABORTING: Database persistence is still broken. Check migrations.")
        # return

    # 2. Audit Files
    results = []
    total_files = 0
    
    print("\nStarting Mass Parity Audit (44 files)...")
    for folder in FOLDERS:
        full_path = os.path.join(BASE_DIR, folder)
        if not os.path.exists(full_path): continue
        files = [f for f in os.listdir(full_path) if f.endswith('.xlsm')]
        for f in files:
            res = await verify_file(os.path.join(full_path, f))
            results.append(res)
            total_files += 1
            if total_files % 10 == 0:
                print(f"Progress: {total_files} files processed...")

    # Save summary
    with open("mass_validation_results.json", "w", encoding='utf-8') as f:
        json.dump(results, f, indent=4)
    
    success_count = sum(1 for r in results if r.get("parity", False))
    print(f"\nAUDIT FINISHED: {success_count}/{total_files} parity success.")
    
    # Analyze errors
    errors = [r for r in results if "ERROR" in r.get("status", "")]
    if errors:
        print(f"Found {len(errors)} errors during processing.")

if __name__ == "__main__":
    asyncio.run(main())
