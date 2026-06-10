from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import StringIdMixin, TimestampMixin
from app.models.enums import DocumentStatus
from sqlalchemy import Enum


class Category(Base, StringIdMixin, TimestampMixin):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), nullable=True, index=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Document(Base, StringIdMixin, TimestampMixin):
    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_updated_at", "updated_at"),
        Index("ix_documents_owner_id", "owner_id"),
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    content_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    content_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[str | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    owner_name: Mapped[str] = mapped_column(String(100), nullable=False)
    owner_avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus, name="document_status"), nullable=False, default=DocumentStatus.draft)
    last_opened_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner = relationship("User", back_populates="documents")
    comments = relationship("Comment", back_populates="document", cascade="all, delete-orphan")


class Template(Base, StringIdMixin, TimestampMixin):
    __tablename__ = "templates"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    creator = relationship("User", back_populates="templates")


class DocumentReaction(Base, StringIdMixin):
    __tablename__ = "document_reactions"
    __table_args__ = (UniqueConstraint("document_id", "user_id", "type", name="uq_document_reactions_document_user_type"),)

    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="like")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)


class Comment(Base, StringIdMixin, TimestampMixin):
    __tablename__ = "comments"

    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    document = relationship("Document", back_populates="comments")
    author = relationship("User", back_populates="comments")
