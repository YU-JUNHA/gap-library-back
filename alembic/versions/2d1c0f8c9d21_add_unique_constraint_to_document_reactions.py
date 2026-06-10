"""add unique constraint to document reactions

Revision ID: 2d1c0f8c9d21
Revises: 9c8d2a1f7b10
Create Date: 2026-06-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "2d1c0f8c9d21"
down_revision: Union[str, Sequence[str], None] = "9c8d2a1f7b10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint(
        "uq_document_reactions_document_user_type",
        "document_reactions",
        ["document_id", "user_id", "type"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_document_reactions_document_user_type", "document_reactions", type_="unique")
