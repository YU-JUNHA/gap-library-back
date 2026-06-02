"""add document content path

Revision ID: 7b0d8c6e2f44
Revises: 1f4b7c2a9d31
Create Date: 2026-06-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7b0d8c6e2f44"
down_revision: Union[str, Sequence[str], None] = "1f4b7c2a9d31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS content_path VARCHAR(1024)")
    op.execute("UPDATE documents SET content_path = 'documents/' || id || '.md' WHERE content_path IS NULL")
    op.execute("ALTER TABLE documents ALTER COLUMN content_path SET NOT NULL")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("documents", "content_path")
