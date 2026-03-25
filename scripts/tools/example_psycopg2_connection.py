"""
Example: Direct Supabase PostgreSQL connection with psycopg2 (synchronous)

This is an example of connecting directly to Supabase PostgreSQL database
using psycopg2 (synchronous driver) instead of the async client.

For the FastAPI application, we use asyncpg (async driver).
This example shows the basic synchronous approach as requested.

Run with:
  pip install psycopg2-binary python-dotenv
  python example_psycopg2_connection.py
"""
import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Fetch DATABASE_URL from .env
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in .env file")
    print("   Create a .env file with:")
    print("   DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-ID].supabase.co:5432/postgres")
    exit(1)

try:
    # Parse connection string
    print(f"🔍 Connecting to Supabase PostgreSQL...")
    
    # Direct connection using psycopg2
    connection = psycopg2.connect(DATABASE_URL)
    print("✅ Connection successful!")
    
    # Create a cursor to execute SQL queries
    cursor = connection.cursor()
    
    # Example 1: Get current time
    print("\n📋 Example 1: Get current time from Postgres")
    cursor.execute("SELECT NOW();")
    result = cursor.fetchone()
    print(f"   Current Time: {result[0]}")
    
    # Example 2: List all tables
    print("\n📋 Example 2: List all tables")
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' ORDER BY table_name;
    """)
    tables = cursor.fetchall()
    print(f"   Found {len(tables)} tables:")
    for table in tables:
        print(f"      - {table[0]}")
    
    # Example 3: Get cables count
    print("\n📋 Example 3: Count cables in database")
    try:
        cursor.execute("SELECT COUNT(*) FROM cabos;")
        count = cursor.fetchone()
        print(f"   Cables in database: {count[0]}")
    except psycopg2.Error as e:
        print(f"   ⚠️  Cabos table not found (needs migration)")
    
    # Example 4: Insert new cable (if table exists)
    print("\n📋 Example 4: Insert new cable")
    try:
        cursor.execute(
            """INSERT INTO cabos (nome, diametro, peso) 
               VALUES (%s, %s, %s) RETURNING id, nome;""",
            ("Test Cable 123mm", 0.0123, 0.456)
        )
        result = cursor.fetchone()
        connection.commit()
        print(f"   ✅ Inserted cable ID {result[0]}: {result[1]}")
    except psycopg2.errors.UniqueViolation:
        print(f"   ⚠️  Cable already exists (duplicate name)")
        connection.rollback()
    except psycopg2.Error as e:
        print(f"   ⚠️  Error: {e}")
        connection.rollback()
    
    # Example 5: Fetch all cables
    print("\n📋 Example 5: Fetch all cables")
    try:
        cursor.execute("SELECT id, nome, diametro, peso FROM cabos ORDER BY nome LIMIT 5;")
        cabos = cursor.fetchall()
        print(f"   First 5 cables:")
        for cabo in cabos:
            print(f"      ID {cabo[0]}: {cabo[1]} (Ø {cabo[2]}mm, {cabo[3]}kg/m)")
    except psycopg2.Error as e:
        print(f"   ⚠️  Error: {e}")
    
    # Close the cursor and connection
    cursor.close()
    connection.close()
    print("\n✅ Connection closed.")

except psycopg2.OperationalError as e:
    print(f"❌ Failed to connect to database: {e}")
    print("\n   Troubleshooting:")
    print("   1. Check DATABASE_URL is correct in .env")
    print("   2. Verify your Supabase project is running")
    print("   3. Check your network connection")

except Exception as e:
    print(f"❌ Error: {e}")
