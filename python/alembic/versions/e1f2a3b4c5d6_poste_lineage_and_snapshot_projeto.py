"""poste_lineage_and_snapshot_projeto

Revision ID: e1f2a3b4c5d6
Revises: b7c8d9e0f1a2
Create Date: 2026-03-28 10:36:00.000000

Context
-------
A physical pole (Poste) may appear in multiple Projects over time.
Project Y can start from a Poste that already exists in Project X.
This migration adds two columns to support full cross-project lineage
and rich audit trails:

1. ``pontos.poste_origem_id``
   Self-referential FK (nullable).  When a Poste in Project Y "inherits"
   from a Poste in Project X, this field points to the ancestor.  The chain
   of ``poste_origem_id`` links forms the full lineage of that physical pole
   across all projects.

2. ``calculos_snapshots.projeto_id``
   Direct reference to the Project that triggered each calculation.
   Without this, you would need to join pontos to find the project, which
   is ambiguous when the same physical pole appears in multiple projects.
   With it, every snapshot is self-describing for audit purposes.
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, Sequence[str], None] = "b7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Self-referential lineage link on pontos
    op.execute(
        """
        ALTER TABLE pontos
            ADD COLUMN IF NOT EXISTS poste_origem_id UUID
                REFERENCES pontos(id) ON DELETE SET NULL;
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_pontos_poste_origem_id
            ON pontos (poste_origem_id)
            WHERE poste_origem_id IS NOT NULL;
        """
    )

    # 2. Project attribution on every calculation snapshot
    op.execute(
        """
        ALTER TABLE calculos_snapshots
            ADD COLUMN IF NOT EXISTS projeto_id UUID
                REFERENCES projetos(id) ON DELETE SET NULL;
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_calculos_snapshots_projeto_id
            ON calculos_snapshots (projeto_id, calculado_em DESC)
            WHERE projeto_id IS NOT NULL;
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_calculos_snapshots_projeto_id;")
    op.execute(
        "ALTER TABLE calculos_snapshots DROP COLUMN IF EXISTS projeto_id;"
    )
    op.execute("DROP INDEX IF EXISTS ix_pontos_poste_origem_id;")
    op.execute(
        "ALTER TABLE pontos DROP COLUMN IF EXISTS poste_origem_id;"
    )
