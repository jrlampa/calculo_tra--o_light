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
   
   O arquivo contém 5 versões sequenciais:
   - v001: tabelas lookup (cabos, postes, redes, normas_regras) + RLS public SELECT
   - v002: tabelas transacionais (projetos, pontos, niveis_calculo, travessias, resultados_calculo)
   - v003: hardening RLS — adiciona owner_id a projetos, políticas owner-scoped, FORCE RLS
   - v004: tabela schema_migrations + índices canônicos (idempotente)
   - v005: remove bypass admin nas tabelas transacionais, recria policies owner-only estritas,
           adiciona índices de paginação/listagem e unicidade normalizada em lookups
   
   A tabela schema_migrations rastreia versões aplicadas. Se re-executar o arquivo
   após a primeira aplicação, v004 e v005 detectam versão já aplicada via
   schema_migrations e pulam sem erro. v001-v003 usam IF NOT EXISTS / ON CONFLICT.
   
   Creates tables:
   - schema_migrations (controle de versão de migrações)
   - cabos (cables)
   - postes (poles)
   - redes (network types)
   - normas_regras (standards/rules)
   - projetos (cabeçalho do projeto — isolado por owner_id)
   - pontos (postes individuais por projeto)
   - niveis_calculo (MT1, MT2, BT, BTZ, RAL por ponto)
   - travessias (T1..T4 por nível)
   - resultados_calculo (cache de resultados por ponto)

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

Tabelas de referência (cabos, postes, redes, normas_regras):
  SELECT: público (qualquer usuário autenticado ou anônimo pode ler)
  INSERT/UPDATE/DELETE: bloqueado por RLS — apenas service_role key bypassa

Tabelas transacionais (projetos, pontos, niveis_calculo, travessias, resultados_calculo):
  Isolamento por owner_id: cada usuário só acessa seus próprios registros.
  A coluna owner_id em projetos é preenchida automaticamente com auth.uid().
  Pontos e tabelas filhas são isolados via JOIN hierárquico a projetos.owner_id.
Políticas owner-only estritas: não há bypass administrativo por claim JWT.
FORCE RLS ativo: bloqueia até o table owner sem policy explícita (v003-v005).

MIGRATION APPLY + SANITY CHECKS (v005)
=====================================

Após executar o conteúdo de python/db/migrations.sql no SQL Editor:

1) Verifique versões aplicadas

    SELECT version, applied_at
    FROM schema_migrations
    WHERE version IN ('v001', 'v002', 'v003', 'v004', 'v005')
    ORDER BY version;

    Esperado: v005 presente.

2) Sanity check de policies transacionais (sem owner_or_admin)

    SELECT schemaname, tablename, policyname, cmd
    FROM pg_policies
    WHERE schemaname = 'public'
       AND tablename IN ('projetos', 'pontos', 'niveis_calculo', 'travessias', 'resultados_calculo')
    ORDER BY tablename, policyname;

    Esperado:
    - policies com sufixo owner_only para SELECT/INSERT/UPDATE/DELETE.
    - ausência de policies owner_or_admin.

3) Sanity check de FORCE RLS

    SELECT relname, relforcerowsecurity
    FROM pg_class
    WHERE relname IN ('projetos', 'pontos', 'niveis_calculo', 'travessias', 'resultados_calculo')
    ORDER BY relname;

    Esperado: relforcerowsecurity = true para todas.

4) Sanity check de índices v005

    SELECT indexname, indexdef
    FROM pg_indexes
    WHERE schemaname = 'public'
       AND indexname IN (
          'idx_projetos_owner_atualizado_em_desc',
          'idx_projetos_atualizado_em_desc',
          'idx_postes_tipo_modelo',
          'idx_normas_regras_categoria_titulo',
          'uq_cabos_nome_norm',
          'uq_redes_tipo_norm',
          'uq_postes_tipo_modelo_norm',
          'uq_normas_regras_categoria_titulo_arquivo_norm'
       )
    ORDER BY indexname;

    Esperado: todos os índices acima presentes.

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
