import asyncio
import os
import sys

# Add python directory to path
sys.path.insert(0, os.getcwd())

from db.pool import initialize_db_pool, db_pool

async def check():
    await initialize_db_pool()
    try:
        # Check applied migrations
        try:
            rows = await db_pool.execute("SELECT version_num FROM alembic_version")
            print(f"Applied migrations: {[r['version_num'] for r in rows]}")
        except Exception as e:
            print(f"Alembic version table error (maybe doesn't exist): {e}")
        
        # Check if projetos exists
        exists = await db_pool.execute_val("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'projetos'
            );
        """)
        print(f"Projetos table exists: {exists}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await db_pool.close()

if __name__ == "__main__":
    asyncio.run(check())
