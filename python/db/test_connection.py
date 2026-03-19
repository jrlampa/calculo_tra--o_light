"""Test Supabase PostgreSQL connection."""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


async def test_connection():
    """Test direct connection to Supabase PostgreSQL."""
    try:
        import asyncpg
        
        database_url = os.getenv("DATABASE_URL", "")
        
        if not database_url:
            print("❌ DATABASE_URL not configured in .env")
            return False
        
        print(f"🔍 Testing connection to Supabase PostgreSQL...")
        
        # Single connection test
        conn = await asyncpg.connect(database_url)
        result = await conn.fetchval("SELECT NOW();")
        print(f"✅ Connection successful!")
        print(f"   Current Time: {result}")
        await conn.close()
        
        # Connection pool test
        print(f"\n🔄 Testing connection pool...")
        pool = await asyncpg.create_pool(
            database_url,
            min_size=2,
            max_size=10,
        )
        
        async with pool.acquire() as conn:
            tables = await conn.fetch(
                """SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' ORDER BY table_name;"""
            )
            print(f"✅ Pool connection successful!")
            print(f"   Tables found: {len(tables)}")
            for table in tables:
                print(f"      - {table['table_name']}")
        
        await pool.close()
        return True
    
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    exit(0 if success else 1)
