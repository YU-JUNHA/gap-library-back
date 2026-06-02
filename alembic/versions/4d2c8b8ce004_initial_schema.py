"""initial schema

Revision ID: 4d2c8b8ce004
Revises: 
Create Date: 2026-06-01 17:06:17.858905

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '4d2c8b8ce004'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    user_role = sa.Enum("admin", "member", name="user_role")
    signup_request_status = sa.Enum("pending", "approved", "rejected", name="signup_request_status")
    document_status = sa.Enum("draft", "published", name="document_status")

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("organization", sa.String(length=255), nullable=True),
        sa.Column("avatar_url", sa.String(length=1024), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "categories",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("parent_id", sa.String(length=50), nullable=True),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["categories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_categories_parent_id", "categories", ["parent_id"], unique=False)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("user_id", sa.String(length=50), nullable=False),
        sa.Column("token", sa.String(length=1024), nullable=False),
        sa.Column("revoked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token", name="uq_refresh_tokens_token"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"], unique=False)

    op.create_table(
        "signup_requests",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("invite_code", sa.String(length=100), nullable=True),
        sa.Column("status", signup_request_status, nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_signup_requests_email", "signup_requests", ["email"], unique=False)
    op.create_index("ix_signup_requests_status", "signup_requests", ["status"], unique=False)

    op.create_table(
        "documents",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("category_id", sa.String(length=50), nullable=True),
        sa.Column("owner_id", sa.String(length=50), nullable=False),
        sa.Column("status", document_status, nullable=False),
        sa.Column("last_opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_documents_owner_id", "documents", ["owner_id"], unique=False)
    op.create_index("ix_documents_updated_at", "documents", ["updated_at"], unique=False)

    op.create_table(
        "templates",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_templates_created_by", "templates", ["created_by"], unique=False)

    op.create_table(
        "comments",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("document_id", sa.String(length=50), nullable=False),
        sa.Column("author_id", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_comments_author_id", "comments", ["author_id"], unique=False)
    op.create_index("ix_comments_document_id", "comments", ["document_id"], unique=False)

    op.create_table(
        "document_reactions",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("document_id", sa.String(length=50), nullable=False),
        sa.Column("user_id", sa.String(length=50), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_document_reactions_document_id", "document_reactions", ["document_id"], unique=False)
    op.create_index("ix_document_reactions_user_id", "document_reactions", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_document_reactions_user_id", table_name="document_reactions")
    op.drop_index("ix_document_reactions_document_id", table_name="document_reactions")
    op.drop_table("document_reactions")

    op.drop_index("ix_comments_document_id", table_name="comments")
    op.drop_index("ix_comments_author_id", table_name="comments")
    op.drop_table("comments")

    op.drop_index("ix_templates_created_by", table_name="templates")
    op.drop_table("templates")

    op.drop_index("ix_documents_updated_at", table_name="documents")
    op.drop_index("ix_documents_owner_id", table_name="documents")
    op.drop_table("documents")

    op.drop_index("ix_signup_requests_status", table_name="signup_requests")
    op.drop_index("ix_signup_requests_email", table_name="signup_requests")
    op.drop_table("signup_requests")

    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_index("ix_categories_parent_id", table_name="categories")
    op.drop_table("categories")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
