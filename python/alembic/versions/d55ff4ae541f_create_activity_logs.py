"""create_activity_logs

Revision ID: d55ff4ae541f
Revises: ff3afec586b4
Create Date: 2026-03-22 11:18:17.709305

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd55ff4ae541f'
down_revision: Union[str, Sequence[str], None] = 'ff3afec586b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema without FK to bypass resolution issue."""
    op.execute("""
        CREATE TABLE activity_logs (
            id UUID PRIMARY KEY,
            projeto_id UUID,
            user_id UUID,
            activity_type VARCHAR(50) NOT NULL,
            details JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX ix_activity_logs_projeto_id ON activity_logs (projeto_id);")
    op.execute("CREATE INDEX ix_activity_logs_user_id ON activity_logs (user_id);")

def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE activity_logs;")
