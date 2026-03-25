
import os
import asyncio
from db.pool import initialize_db_pool, db_pool
from dotenv import load_dotenv

async def main():
    load_dotenv()
    await initialize_db_pool()
    
    print("--- SCHEMAS & TABLES ---")
    schemas = await db_pool.fetch_all("SELECT schema_name FROM information_schema.schemata")
    for s in schemas:
        s_name = s['schema_name']
        if s_name in ['information_schema', 'pg_catalog']: continue
        print(f"Schema: {s_name}")
        tables = await db_pool.fetch_all(f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{s_name}'")
        for t in tables:
            t_name = t['table_name']
            print(f"  Table: {t_name}")
            cols = await db_pool.fetch_all(f"SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema = '{s_name}' AND table_name = '{t_name}'")
            for c in cols:
                print(f"    - {c['column_name']} ({c['data_type']}) Nullable: {c['is_nullable']}")

    await db_pool.close()

if __name__ == "__main__":
    asyncio.run(main())
