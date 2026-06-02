"""add document list indexes

Revision ID: 1f4b7c2a9d31
Revises: 9c8d2a1f7b10
Create Date: 2026-06-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "1f4b7c2a9d31"
down_revision: Union[str, Sequence[str], None] = "9c8d2a1f7b10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE INDEX IF NOT EXISTS ix_documents_created_at ON documents (created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_documents_category_id ON documents (category_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_documents_owner_name ON documents (owner_name)")
    op.execute(
        """
        CREATE INDEX ix_documents_search_tsv
        ON documents
        USING gin (
            to_tsvector(
                'simple',
                coalesce(title, '') || ' ' || coalesce(summary, '') || ' ' || coalesce(content_text, '')
            )
        )
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS ix_documents_search_tsv")
    op.execute("DROP INDEX IF EXISTS ix_documents_owner_name")
    op.execute("DROP INDEX IF EXISTS ix_documents_category_id")
    op.execute("DROP INDEX IF EXISTS ix_documents_created_at")
