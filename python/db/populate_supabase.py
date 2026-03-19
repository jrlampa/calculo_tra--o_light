import os
import psycopg2
from dotenv import load_dotenv
import sys
from pathlib import Path
from urllib.parse import urlparse, quote_plus

# Adiciona o diretório pai ao path para importar as tabelas traduzidas
sys.path.append(str(Path(__file__).parent.parent))
from translated.plan1_tables import CABOS_TABLE, POSTE_TABLE, REDE_TABLE

def populate():
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("Erro: DATABASE_URL não encontrada no .env")
        return

    # Robust parse handling special chars in password
    from urllib.parse import urlparse, unquote

    try:
        p = urlparse(db_url)
        user = p.username
        password = p.password
        host = p.hostname
        port = p.port or 5432
        dbname = p.path.lstrip('/')

        # Fallback manual split if urlparse fails on some characters
        if not user or not password:
             # Manual split as a second layer
             schema_part, rest = db_url.split("://")
             credentials, rest = rest.split("@")
             user, password = credentials.split(":", 1)
             host_port, dbname = rest.split("/")
             host, port = host_port.split(":") if ":" in host_port else (host_port, 5432)

        # Ensure password is literal if it came from urlparse (it might be encoded)
        if password and '%' in password and '%25' not in password:
             # It's likely already literal from .env
             pass

        print(f"Tentando conectar ao host: {host}")
        conn = psycopg2.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database=dbname,
            connect_timeout=10
        )
        cur = conn.cursor()

        print("--- Populando Cabos ---")
        # Limpa tabela se necessário (opcional, dependendo do requisito)
        # cur.execute("TRUNCATE TABLE cabos CASCADE;")
        
        for row in CABOS_TABLE:
            nome = row[0]
            diametro = row[1]
            peso = row[2]
            cur.execute(
                "INSERT INTO cabos (nome, diametro, peso) VALUES (%s, %s, %s) ON CONFLICT (nome) DO UPDATE SET diametro = EXCLUDED.diametro, peso = EXCLUDED.peso;",
                (nome, diametro, peso)
            )
        
        print(f"Inseridos/Atualizados {len(CABOS_TABLE)} cabos.")

        print("--- Populando Redes ---")
        for row in REDE_TABLE:
            tipo = row[0]
            # Redes table uses 'descricao'
            desc = f"Rede {tipo}"
            cur.execute(
                "INSERT INTO redes (tipo, descricao) VALUES (%s, %s) ON CONFLICT (tipo) DO UPDATE SET descricao = EXCLUDED.descricao;",
                (tipo, desc)
            )

        print("--- Populando Postes ---")
        count_postes = 0
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
                  except:
                    pass
                
                # Check if 'excentricidade' column exists, otherwise use 'carga_admissivel_dan'
                cur.execute(
                    "INSERT INTO postes (tipo, modelo, altura_m, carga_admissivel_dan) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING;",
                    (tipo, label, altura, carga)
                )
                count_postes += 1
        
        print(f"Inseridos {count_postes} modelos de postes.")

        conn.commit()
        cur.close()
        conn.close()
        print("✅ Supabase populado com sucesso!")

    except Exception as e:
        print(f"❌ Erro ao popular Supabase: {e}")

if __name__ == "__main__":
    populate()
