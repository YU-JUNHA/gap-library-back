from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.base import StringIdMixin
from app.models.enums import SignupRequestStatus


class SignupRequest(Base, StringIdMixin):
    __tablename__ = "signup_requests"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    invite_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[SignupRequestStatus] = mapped_column(
        Enum(SignupRequestStatus, name="signup_request_status"), nullable=False, default=SignupRequestStatus.pending, index=True
    )
    requested_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    reviewed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
