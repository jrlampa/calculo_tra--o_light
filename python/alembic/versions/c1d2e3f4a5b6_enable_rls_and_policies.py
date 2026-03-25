"""Enable RLS and create access policies

Revision ID: c1d2e3f4a5b6
Revises: d55ff4ae541f
Create Date: 2026-03-24 23:00:00.000000

This migration enables Row-Level Security (RLS) on all tables and creates
comprehensive access policies to ensure users can only access their own data.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, Sequence[str], None] = 'd55ff4ae541f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enable RLS on all tables and create access policies."""
    
    # ── Enable RLS on projetos table ─────────────────────────────────────
    op.execute("ALTER TABLE projetos ENABLE ROW LEVEL SECURITY;")
    
    # Policy: SELECT - User can view their own projects
    op.execute("""
        CREATE POLICY projetos_select_own
        ON projetos FOR SELECT
        USING (auth.uid() = owner_id OR EXISTS (
            SELECT 1 FROM activity_logs 
            WHERE activity_logs.user_id = auth.uid() 
            AND activity_logs.projeto_id = projetos.id
        ))
    """)
    
    # Policy: INSERT - User can create projects (their own)
    op.execute("""
        CREATE POLICY projetos_insert
        ON projetos FOR INSERT
        WITH CHECK (auth.uid() = owner_id)
    """)
    
    # Policy: UPDATE - User can update their own projects
    op.execute("""
        CREATE POLICY projetos_update_own
        ON projetos FOR UPDATE
        USING (auth.uid() = owner_id)
        WITH CHECK (auth.uid() = owner_id)
    """)
    
    # Policy: DELETE - User can delete their own projects
    op.execute("""
        CREATE POLICY projetos_delete_own
        ON projetos FOR DELETE
        USING (auth.uid() = owner_id)
    """)

    # ── Enable RLS on pontos table ──────────────────────────────────────
    op.execute("ALTER TABLE pontos ENABLE ROW LEVEL SECURITY;")
    
    # Policy: SELECT - User can view points in their projects
    op.execute("""
        CREATE POLICY pontos_select_own
        ON pontos FOR SELECT
        USING (EXISTS (
            SELECT 1 FROM projetos
            WHERE projetos.id = pontos.projeto_id
            AND (auth.uid() = projetos.owner_id OR
                 auth.uid() = (SELECT user_id FROM activity_logs 
                              WHERE activity_logs.projeto_id = projetos.id LIMIT 1))
        ))
    """)
    
    # Policy: INSERT - User can create points in their projects
    op.execute("""
        CREATE POLICY pontos_insert
        ON pontos FOR INSERT
        WITH CHECK (EXISTS (
            SELECT 1 FROM projetos
            WHERE projetos.id = pontos.projeto_id
            AND auth.uid() = projetos.owner_id
        ))
    """)
    
    # Policy: UPDATE - User can update points in their projects
    op.execute("""
        CREATE POLICY pontos_update_own
        ON pontos FOR UPDATE
        USING (EXISTS (
            SELECT 1 FROM projetos
            WHERE projetos.id = pontos.projeto_id
            AND auth.uid() = projetos.owner_id
        ))
        WITH CHECK (EXISTS (
            SELECT 1 FROM projetos
            WHERE projetos.id = pontos.projeto_id
            AND auth.uid() = projetos.owner_id
        ))
    """)
    
    # Policy: DELETE - User can delete points in their projects
    op.execute("""
        CREATE POLICY pontos_delete_own
        ON pontos FOR DELETE
        USING (EXISTS (
            SELECT 1 FROM projetos
            WHERE projetos.id = pontos.projeto_id
            AND auth.uid() = projetos.owner_id
        ))
    """)

    # ── Enable RLS on niveis_calculo table ──────────────────────────────
    op.execute("ALTER TABLE niveis_calculo ENABLE ROW LEVEL SECURITY;")
    
    # Policy: SELECT - User can view levels in their project points
    op.execute("""
        CREATE POLICY niveis_calculo_select_own
        ON niveis_calculo FOR SELECT
        USING (EXISTS (
            SELECT 1 FROM pontos
            INNER JOIN projetos ON projetos.id = pontos.projeto_id
            WHERE niveis_calculo.ponto_id = pontos.id
            AND auth.uid() = projetos.owner_id
        ))
    """)
    
    # Policy: INSERT
    op.execute("""
        CREATE POLICY niveis_calculo_insert
        ON niveis_calculo FOR INSERT
        WITH CHECK (EXISTS (
            SELECT 1 FROM pontos
            INNER JOIN projetos ON projetos.id = pontos.projeto_id
            WHERE niveis_calculo.ponto_id = pontos.id
            AND auth.uid() = projetos.owner_id
        ))
    """)
    
    # Policy: UPDATE
    op.execute("""
        CREATE POLICY niveis_calculo_update_own
        ON niveis_calculo FOR UPDATE
        USING (EXISTS (
            SELECT 1 FROM pontos
            INNER JOIN projetos ON projetos.id = pontos.projeto_id
            WHERE niveis_calculo.ponto_id = pontos.id
            AND auth.uid() = projetos.owner_id
        ))
        WITH CHECK (EXISTS (
            SELECT 1 FROM pontos
            INNER JOIN projetos ON projetos.id = pontos.projeto_id
            WHERE niveis_calculo.ponto_id = pontos.id
            AND auth.uid() = projetos.owner_id
        ))
    """)
    
    # Policy: DELETE
    op.execute("""
        CREATE POLICY niveis_calculo_delete_own
        ON niveis_calculo FOR DELETE
        USING (EXISTS (
            SELECT 1 FROM pontos
            INNER JOIN projetos ON projetos.id = pontos.projeto_id
            WHERE niveis_calculo.ponto_id = pontos.id
            AND auth.uid() = projetos.owner_id
        ))
    """)

    # ── Enable RLS on travessias table ──────────────────────────────────
    op.execute("ALTER TABLE travessias ENABLE ROW LEVEL SECURITY;")
    
    # Policy: SELECT - User can view traversals in their project calculations
    op.execute("""
        CREATE POLICY travessias_select_own
        ON travessias FOR SELECT
        USING (EXISTS (
            SELECT 1 FROM niveis_calculo
            INNER JOIN pontos ON pontos.id = niveis_calculo.ponto_id
            INNER JOIN projetos ON projetos.id = pontos.projeto_id
            WHERE travessias.nivel_id = niveis_calculo.id
            AND auth.uid() = projetos.owner_id
        ))
    """)
    
    # Policy: INSERT
    op.execute("""
        CREATE POLICY travessias_insert
        ON travessias FOR INSERT
        WITH CHECK (EXISTS (
            SELECT 1 FROM niveis_calculo
            INNER JOIN pontos ON pontos.id = niveis_calculo.ponto_id
            INNER JOIN projetos ON projetos.id = pontos.projeto_id
            WHERE travessias.nivel_id = niveis_calculo.id
            AND auth.uid() = projetos.owner_id
        ))
    """)
    
    # Policy: UPDATE
    op.execute("""
        CREATE POLICY travessias_update_own
        ON travessias FOR UPDATE
        USING (EXISTS (
            SELECT 1 FROM niveis_calculo
            INNER JOIN pontos ON pontos.id = niveis_calculo.ponto_id
            INNER JOIN projetos ON projetos.id = pontos.projeto_id
            WHERE travessias.nivel_id = niveis_calculo.id
            AND auth.uid() = projetos.owner_id
        ))
        WITH CHECK (EXISTS (
            SELECT 1 FROM niveis_calculo
            INNER JOIN pontos ON pontos.id = niveis_calculo.ponto_id
            INNER JOIN projetos ON projetos.id = pontos.projeto_id
            WHERE travessias.nivel_id = niveis_calculo.id
            AND auth.uid() = projetos.owner_id
        ))
    """)
    
    # Policy: DELETE
    op.execute("""
        CREATE POLICY travessias_delete_own
        ON travessias FOR DELETE
        USING (EXISTS (
            SELECT 1 FROM niveis_calculo
            INNER JOIN pontos ON pontos.id = niveis_calculo.ponto_id
            INNER JOIN projetos ON projetos.id = pontos.projeto_id
            WHERE travessias.nivel_id = niveis_calculo.id
            AND auth.uid() = projetos.owner_id
        ))
    """)

    # ── Enable RLS on resultados_calculo table ──────────────────────────
    op.execute("ALTER TABLE resultados_calculo ENABLE ROW LEVEL SECURITY;")
    
    # Policy: SELECT
    op.execute("""
        CREATE POLICY resultados_calculo_select_own
        ON resultados_calculo FOR SELECT
        USING (EXISTS (
            SELECT 1 FROM pontos
            INNER JOIN projetos ON projetos.id = pontos.projeto_id
            WHERE resultados_calculo.ponto_id = pontos.id
            AND auth.uid() = projetos.owner_id
        ))
    """)
    
    # Policy: INSERT
    op.execute("""
        CREATE POLICY resultados_calculo_insert
        ON resultados_calculo FOR INSERT
        WITH CHECK (EXISTS (
            SELECT 1 FROM pontos
            INNER JOIN projetos ON projetos.id = pontos.projeto_id
            WHERE resultados_calculo.ponto_id = pontos.id
            AND auth.uid() = projetos.owner_id
        ))
    """)
    
    # Policy: UPDATE
    op.execute("""
        CREATE POLICY resultados_calculo_update_own
        ON resultados_calculo FOR UPDATE
        USING (EXISTS (
            SELECT 1 FROM pontos
            INNER JOIN projetos ON projetos.id = pontos.projeto_id
            WHERE resultados_calculo.ponto_id = pontos.id
            AND auth.uid() = projetos.owner_id
        ))
        WITH CHECK (EXISTS (
            SELECT 1 FROM pontos
            INNER JOIN projetos ON projetos.id = pontos.projeto_id
            WHERE resultados_calculo.ponto_id = pontos.id
            AND auth.uid() = projetos.owner_id
        ))
    """)
    
    # Policy: DELETE
    op.execute("""
        CREATE POLICY resultados_calculo_delete_own
        ON resultados_calculo FOR DELETE
        USING (EXISTS (
            SELECT 1 FROM pontos
            INNER JOIN projetos ON projetos.id = pontos.projeto_id
            WHERE resultados_calculo.ponto_id = pontos.id
            AND auth.uid() = projetos.owner_id
        ))
    """)

    # ── Enable RLS on lookup tables (read-only for all authenticated users)
    for table in ['cabos', 'postes', 'redes', 'normas_regras']:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        
        # SELECT policy: Any authenticated user can read lookup tables
        op.execute(f"""
            CREATE POLICY {table}_select_all
            ON {table} FOR SELECT
            USING (auth.role() = 'authenticated')
        """)
        
        # INSERT, UPDATE, DELETE: Only admins (would need admin flag in auth)
        # For now, deny write access to non-superusers
        op.execute(f"""
            CREATE POLICY {table}_deny_write
            ON {table} FOR INSERT
            WITH CHECK (FALSE)
        """)
        op.execute(f"""
            CREATE POLICY {table}_deny_update
            ON {table} FOR UPDATE
            WITH CHECK (FALSE)
        """)
        op.execute(f"""
            CREATE POLICY {table}_deny_delete
            ON {table} FOR DELETE
            USING (FALSE)
        """)

    # ── Enable RLS on activity_logs (user can view their own activity)
    op.execute("ALTER TABLE activity_logs ENABLE ROW LEVEL SECURITY;")
    
    # Policy: SELECT own activity logs
    op.execute("""
        CREATE POLICY activity_logs_select_own
        ON activity_logs FOR SELECT
        USING (auth.uid() = user_id)
    """)
    
    # Policy: INSERT own activity logs
    op.execute("""
        CREATE POLICY activity_logs_insert
        ON activity_logs FOR INSERT
        WITH CHECK (auth.uid() = user_id)
    """)


def downgrade() -> None:
    """Disable RLS and drop all policies."""
    
    # Drop all policies
    for table in ['projetos', 'pontos', 'niveis_calculo', 'travessias', 
                  'resultados_calculo', 'cabos', 'postes', 'redes', 
                  'normas_regras', 'activity_logs']:
        op.execute(f"DROP POLICY IF EXISTS {table}_select_own ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_select_all ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_insert ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_update_own ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_delete_own ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_deny_write ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_deny_update ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_deny_delete ON {table};")
        
        # Disable RLS
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
