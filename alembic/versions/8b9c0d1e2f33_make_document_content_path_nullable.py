"""make document content_path nullable

Revision ID: 8b9c0d1e2f33
Revises: 6a7b8c9d0e11
Create Date: 2026-06-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "8b9c0d1e2f33"
down_revision: Union[str, Sequence[str], None] = "6a7b8c9d0e11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE documents ALTER COLUMN content_path DROP NOT NULL")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("UPDATE documents SET content_path = 'documents/' || id || '.md' WHERE content_path IS NULL")
    op.execute("ALTER TABLE documents ALTER COLUMN content_path SET NOT NULL")
