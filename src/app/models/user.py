from sqlalchemy import Boolean, DateTime, Enum, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import StringIdMixin, TimestampMixin
from app.models.enums import UserRole


class User(Base, StringIdMixin, TimestampMixin):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), nullable=False, default=UserRole.member)
    organization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    last_login_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    documents = relationship("Document", back_populates="owner")
    templates = relationship("Template", back_populates="creator")
    comments = relationship("Comment", back_populates="author")


class RefreshToken(Base, StringIdMixin):
    __tablename__ = "refresh_tokens"
    __table_args__ = (UniqueConstraint("token", name="uq_refresh_tokens_token"),)

    user_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    token: Mapped[str] = mapped_column(String(1024), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
