"""add_calculos_snapshots_table

Revision ID: a1b2c3d4e5f6
Revises: d55ff4ae541f
Create Date: 2026-03-25 14:00:00.000000

This migration adds the calculos_snapshots table for storing append-only
calculation history. Enables audit trail and recovery of past calculations.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'd55ff4ae541f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create calculos_snapshots table for append-only calculation history."""
    op.execute("""
        CREATE TABLE calculos_snapshots (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            poste_id UUID NOT NULL REFERENCES pontos(id) ON DELETE CASCADE,
            resultado_json TEXT NOT NULL,
            calculado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            calculado_por VARCHAR(100),
            status VARCHAR(20) NOT NULL DEFAULT 'draft',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    
    # Indexes for common queries
    op.execute("""
        CREATE INDEX ix_calculos_snapshots_poste_id 
        ON calculos_snapshots (poste_id, calculado_em DESC);
    """)
    
    op.execute("""
        CREATE INDEX ix_calculos_snapshots_status 
        ON calculos_snapshots (status, calculado_em DESC);
    """)


def downgrade() -> None:
    """Drop calculos_snapshots table."""
    op.execute("DROP TABLE IF EXISTS calculos_snapshots CASCADE;")
