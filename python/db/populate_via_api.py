import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Adiciona o diretório pai ao path para importar as tabelas traduzidas
sys.path.append(str(Path(__file__).parent.parent))
from translated.plan1_tables import CABOS_TABLE, POSTE_TABLE, REDE_TABLE

def populate():
    load_dotenv()
    url = os.getenv("VITE_SUPABASE_URL")
    key = os.getenv("VITE_SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("Erro: VITE_SUPABASE_URL ou VITE_SUPABASE_ANON_KEY não encontradas no .env")
        return

    supabase: Client = create_client(url, key)

    print("--- Populando Cabos via API ---")
    for row in CABOS_TABLE:
        data = {
            "nome": row[0],
            "diametro": row[1],
            "peso": row[2]
        }
        try:
            # Upsert using 'nome' as unique constraint (requires unique constraint in DB)
            res = supabase.table("cabos").upsert(data, on_conflict="nome").execute()
            print(f"✅ Cabo {row[0]} processado.")
        except Exception as e:
            print(f"❌ Erro no cabo {row[0]}: {e}")

    print("--- Populando Redes via API ---")
    for row in REDE_TABLE:
        data = {
            "tipo": row[0],
            "descricao": f"Rede {row[0]}"
        }
        try:
            res = supabase.table("redes").upsert(data, on_conflict="tipo").execute()
            print(f"✅ Rede {row[0]} processada.")
        except Exception as e:
            print(f"❌ Erro na rede {row[0]}: {e}")

    print("--- Populando Postes via API ---")
    for tipo, modelos in POSTE_TABLE.items():
        for row in modelos:
            label = row[0]
            ecc = row[1]
            parts = label.split("/")
            altura = 0
            carga = 0
            if len(parts) >= 2:
                try:
                    altura = float(parts[0].strip().split()[0].replace(',', '.'))
                    carga = float(parts[1].strip().split()[0].replace(',', '.'))
                except: pass
            
            data = {
                "tipo": tipo,
                "modelo": label,
                "altura_m": altura,
                "carga_admissivel_dan": carga
            }
            try:
                # Postes table doesn't have a simple unique constraint for upsert in some migrations
                # We'll use insert and catch conflict if any
                res = supabase.table("postes").insert(data).execute()
                print(f"✅ Poste {label} inserido.")
            except Exception as e:
                print(f"⚠️ Poste {label} talvez já exista ou erro: {e}")

    print("✅ Sincronização via API concluída!")

if __name__ == "__main__":
    populate()
