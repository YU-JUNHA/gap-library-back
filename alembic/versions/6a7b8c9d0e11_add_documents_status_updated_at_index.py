"""add documents status updated_at index

Revision ID: 6a7b8c9d0e11
Revises: 1f4b7c2a9d31
Create Date: 2026-06-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "6a7b8c9d0e11"
down_revision: Union[str, Sequence[str], None] = "1f4b7c2a9d31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_documents_status_updated_at ON documents (status, updated_at)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS ix_documents_status_updated_at")
