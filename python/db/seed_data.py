"""Generate seed data from Excel lookup tables."""
import sys
from pathlib import Path
from typing import List, Dict, Any

# Import tables from translated module
sys.path.insert(0, str(Path(__file__).parent.parent))
from translated.plan1_tables import CABOS_TABLE, POSTE_TABLE, REDE_TABLE


def get_seed_cabos() -> List[Dict[str, Any]]:
    """Convert CABOS_TABLE to seed format for Supabase."""
    return [
        {
            "nome": str(row[0]).strip(),
            "diametro": float(row[1]),
            "peso": float(row[2])
        }
        for row in CABOS_TABLE
    ]


def get_seed_postes() -> List[Dict[str, Any]]:
    """Convert POSTE_TABLE to seed format for Supabase."""
    result = []
    for tipo, models in POSTE_TABLE.items():
        for row in models:
            # Each row is [modelo_label, ecc_value]
            # modelo_label format: "11 m / 600 daN"
            if len(row) >= 2:
                modelo_label = str(row[0]).strip()
                ecc_value = float(row[1])
                
                # Parse the label to extract altura and carga
                parts = modelo_label.split("/")
                altura_m = 11.0  # default
                carga_dan = 600.0  # default
                
                if len(parts) >= 2:
                    try:
                        altura_m = float(parts[0].strip().split()[0])
                        carga_dan = float(parts[1].strip().split()[0])
                    except (ValueError, IndexError):
                        pass
                
                result.append({
                    "tipo": tipo,
                    "modelo": modelo_label,
                    "altura_m": altura_m,
                    "carga_admissivel_dan": carga_dan
                })
    return result


def get_seed_redes() -> List[Dict[str, Any]]:
    """Convert REDE_TABLE to seed format for Supabase."""
    return [
        {
            "tipo": str(row[0]).strip(),
            "descricao": str(row[1]).strip() if len(row) > 1 else None
        }
        for row in REDE_TABLE
    ]


if __name__ == "__main__":
    cabos = get_seed_cabos()
    postes = get_seed_postes()
    redes = get_seed_redes()
    
    print(f"✅ Seed data ready:")
    print(f"   - Cabos: {len(cabos)} entries")
    print(f"   - Postes: {len(postes)} entries")
    print(f"   - Redes: {len(redes)} entries")
    
    # Print as SQL INSERT (for manual insert into Supabase)
    print("\n📋 SQL INSERT statements:\n")
    print("-- Cabos")
    for cabo in cabos:
        nome_escaped = cabo['nome'].replace("'", "''")
        print(f"INSERT INTO cabos (nome, diametro, peso) VALUES ('{nome_escaped}', {cabo['diametro']}, {cabo['peso']});")
    
    print("\n-- Redes")
    for rede in redes:
        tipo_escaped = rede['tipo'].replace("'", "''")
        descricao = f"'{rede['descricao'].replace(chr(34), chr(34)*2)}'" if rede['descricao'] else "NULL"
        print(f"INSERT INTO redes (tipo, descricao) VALUES ('{tipo_escaped}', {descricao});")
