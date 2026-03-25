
import os
import asyncio
from db.pool import initialize_db_pool, db_pool
from dotenv import load_dotenv

async def main():
    load_dotenv()
    await initialize_db_pool()
    
    print("--- Database Structure ---")
    tables = await db_pool.fetch_all("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    for t in tables:
        print(f"Table: {t['table_name']}")
        # Get columns
        cols = await db_pool.fetch_all(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{t['table_name']}'")
        for c in cols:
            print(f"  - {c['column_name']} ({c['data_type']})")

    # Check for recent points
    print("\n--- Recent Points ---")
    points = await db_pool.fetch_all("SELECT id, ponto, tipo_poste, modelo_poste, created_at FROM pontos ORDER BY created_at DESC LIMIT 5")
    for p in points:
        print(f"ID: {p['id']}, Ponto: {p['ponto']}, Poste: {p['tipo_poste']} {p['modelo_poste']}, Created: {p['created_at']}")

    await db_pool.close()

if __name__ == "__main__":
    asyncio.run(main())
