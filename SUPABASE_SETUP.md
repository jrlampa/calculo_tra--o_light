"""
SUPABASE POSTGRESQL CONNECTION - COMPLETE SETUP GUIDE
=====================================================

This guide explains how to connect the application directly to your Supabase PostgreSQL database
using asyncpg (async PostgreSQL driver), which is more efficient than REST API calls.

QUICK START
===========

1. GET YOUR DATABASE URL FROM SUPABASE
   - Log in to https://app.supabase.com
   - Select your project
   - Click "Settings" → "Database"
   - Find "Connection string" and copy the PostgreSQL URL
   - Format: postgresql://postgres:[PASSWORD]@db.[PROJECT-ID].supabase.co:5432/postgres

2. CREATE .env FILE (Copy .env.example first)
   
   .env file content:
   ==================
   DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-ID].supabase.co:5432/postgres
   
   Note: Replace [YOUR-PASSWORD] and [PROJECT-ID] with actual values from Supabase
        DO NOT commit .env to Git (it's in .gitignore)

3. TEST CONNECTION
   
   cd python
   python db/test_connection.py
   
   Expected output:
   ✅ Connection successful!
      Current Time: 2026-03-19 12:34:56.789456+00:00
   ✅ Pool connection successful!
      Tables found: 4
         - cabos
         - normas_regras
         - postes
         - redes

4. RUN SEED DATA (Initialize tables with Excel data)
   
   python db/seed_data.py
   
   Output:
   ✅ Seed data ready:
      - Cabos: 33 entries
      - Postes: 25 entries
      - Redes: 6 entries

5. INITIALIZE DATABASE (Run migrations)
   
   Copy content from: python/db/migrations.sql
   Go to: Supabase → SQL Editor → New Query
   Paste and execute the SQL
   
   Creates tables:
   - cabos (cables)
   - postes (poles)
   - redes (network types)
   - normas_regras (standards/rules)

6. EXTRACT AND POPULATE NORMAS (Optional - extract from LIGHT PDFs)
   
   python db/extract_normas.py
   
   This extracts rules from:
   C:\Users\jonat\OneDrive - IM3 Brasil\LIGHT\Arquivos para auxílio
   
   And auto-inserts into normas_regras table

7. START THE APPLICATION
   
   npm run dev:full
   
   This starts:
   - FastAPI backend on http://localhost:8000
   - React frontend on http://localhost:5173
   - Vite proxy forwards /api calls to backend

API ENDPOINTS (Database CRUD)
============================

GET /admin/cabos
  Returns all cables

POST /admin/cabos?nome=...&diametro=...&peso=...
  Create new cable

DELETE /admin/cabos/{id}
  Delete cable by ID

GET /admin/postes
  Returns all poles

POST /admin/postes?tipo=...&modelo=...&altura_m=...&carga_dan=...
  Create new pole

DELETE /admin/postes/{id}
  Delete pole by ID

GET /admin/redes
  Returns all network types

GET /admin/normas
  Returns all standards/rules

GET /admin/normas?categoria=Padrão%20Compacta
  Return rules by category

GET /admin/normas/categorias
  Return available categories with counts

DATABASE ARCHITECTURE
====================

PostgreSQL Database: postgres
Tables:
1. cabos
   - id: PRIMARY KEY
   - nome: TEXT UNIQUE
   - diametro: FLOAT
   - peso: FLOAT
   - created_at: TIMESTAMP
   - updated_at: TIMESTAMP

2. postes
   - id: PRIMARY KEY
   - tipo: TEXT
   - modelo: TEXT
   - altura_m: FLOAT
   - carga_admissivel_dan: FLOAT
   - created_at: TIMESTAMP
   - updated_at: TIMESTAMP

3. redes
   - id: PRIMARY KEY
   - tipo: TEXT UNIQUE
   - descricao: TEXT
   - created_at: TIMESTAMP
   - updated_at: TIMESTAMP

4. normas_regras
   - id: PRIMARY KEY
   - categoria: TEXT
   - arquivo_origem: TEXT
   - titulo: TEXT
   - descricao: TEXT
   - regra_tecnica: TEXT
   - aplicavel_a: TEXT
   - fonte_referencia: TEXT
   - created_at: TIMESTAMP
   - updated_at: TIMESTAMP

ROW LEVEL SECURITY (RLS)
Each table has RLS enabled with public SELECT policy.
This means anyone can read data, but writes require authentication.

PYTHON CLIENT CODE
=================

Basic Usage:
  from db import get_supabase_client
  
  client = get_supabase_client()
  
  # Fetch all cables
  cabos = await client.fetch_cabos()
  
  # Insert new cable
  result = await client.insert_cabo("397MCM-CA, Nu", 0.0184, 0.558)
  
  # Delete cable
  success = await client.delete_cabo(cable_id)
  
  # Fetch normas by category
  normas = await client.fetch_normas_by_categoria("Padrão Compacta")
  
  # Close connections
  await client.close()

TROUBLESHOOTING
==============

🔴 "DATABASE_URL not configured"
   → Check .env file exists and has correct DATABASE_URL

🔴 "Connection refused"
   → Verify Supabase project is running
   → Check if DATABASE_URL is correct
   → Ensure you're on the correct network

🔴 "Authentication failed"
   → Wrong password in DATABASE_URL
   → Copy fresh URL from Supabase Settings

🔴 "Table does not exist"
   → Run migrations.sql in Supabase SQL Editor
   → Wait for completion

🔴 "asyncpg not installed"
   → pip install asyncpg psycopg2-binary

USEFUL LINKS
===========

Supabase Docs: https://supabase.com/docs
PostgreSQL Docs: https://www.postgresql.org/docs/
asyncpg Docs: https://magicstack.github.io/asyncpg/current/
"""

if __name__ == "__main__":
    print(__doc__)
