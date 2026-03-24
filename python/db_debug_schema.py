import asyncio
import os
import sys

# Add python directory to path
sys.path.insert(0, os.getcwd())

from db.pool import initialize_db_pool, db_pool

async def check():
    await initialize_db_pool()
    try:
        # Check table schema
        rows = await db_pool.execute("""
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_name = 'projetos'
        """)
        for r in rows:
            print(f"Table {r['table_name']} is in schema {r['table_schema']}")
            
        # Check current search path
        path = await db_pool.execute_val("SHOW search_path")
        print(f"Current search_path: {path}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await db_pool.close()

if __name__ == "__main__":
    asyncio.run(check())
