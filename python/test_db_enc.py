import asyncio
import asyncpg
import os
from urllib.parse import quote_plus

async def test():
    # raw password from .env: sisLIGHT100%
    # encoded: sisLIGHT100%25
    base_url = "postgresql://postgres:sisLIGHT100%@db.ywnpfeaswdhyaiyqisao.supabase.co:5432/postgres"
    encoded_url = "postgresql://postgres:sisLIGHT100%25@db.ywnpfeaswdhyaiyqisao.supabase.co:5432/postgres"
    
    print(f"Testing RAW URL...")
    try:
        conn = await asyncpg.connect(base_url, timeout=10)
        print("Success with RAW URL!")
        await conn.close()
    except Exception as e:
        print(f"Failed with RAW URL: {e}")

    print(f"\nTesting ENCODED URL (%25)...")
    try:
        conn = await asyncpg.connect(encoded_url, timeout=10)
        print("Success with ENCODED URL!")
        await conn.close()
    except Exception as e:
        print(f"Failed with ENCODED URL: {e}")

if __name__ == "__main__":
    asyncio.run(test())
