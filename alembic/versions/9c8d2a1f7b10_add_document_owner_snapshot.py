"""add document owner snapshot

Revision ID: 9c8d2a1f7b10
Revises: 4d2c8b8ce004
Create Date: 2026-06-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9c8d2a1f7b10"
down_revision: Union[str, Sequence[str], None] = "4d2c8b8ce004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS owner_name VARCHAR(100)")
    op.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS owner_avatar_url VARCHAR(1024)")

    op.execute(
        """
        UPDATE documents AS d
        SET owner_name = u.name,
            owner_avatar_url = u.avatar_url
        FROM users AS u
        WHERE d.owner_id = u.id
        """
    )

    op.execute("ALTER TABLE documents ALTER COLUMN owner_name SET NOT NULL")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("documents", "owner_avatar_url")
    op.drop_column("documents", "owner_name")
