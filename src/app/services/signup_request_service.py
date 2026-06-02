from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.enums import SignupRequestStatus, UserRole
from app.models.signup_request import SignupRequest
from app.models.user import User
from app.repositories.signup_request_repository import SignupRequestRepository
from app.repositories.user_repository import UserRepository


class SignupRequestService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SignupRequestRepository(db)
        self.user_repo = UserRepository(db)

    @staticmethod
    def ensure_admin(user: User) -> None:
        if user.role != UserRole.admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="관리자 권한이 필요합니다.")

    def create_request(self, *, name: str, email: str, password: str, invite_code: str | None) -> SignupRequest:
        if self.user_repo.get_by_email(email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 가입된 이메일입니다.")

        row = SignupRequest(
            name=name,
            email=email,
            password_hash=get_password_hash(password),
            invite_code=invite_code,
            status=SignupRequestStatus.pending,
            requested_at=datetime.now(timezone.utc),
        )
        return self.repo.create(row)

    def list_pending(self) -> list[SignupRequest]:
        return self.repo.list_pending()

    def approve(self, *, request_id: str, admin_user: User) -> tuple[SignupRequest, User]:
        self.ensure_admin(admin_user)
        row = self.repo.get(request_id)
        if not row:
            raise HTTPException(status_code=404, detail="가입 요청을 찾을 수 없습니다.")
        if row.status != SignupRequestStatus.pending:
            raise HTTPException(status_code=409, detail="이미 처리된 가입 요청입니다.")
        if self.user_repo.get_by_email(row.email):
            raise HTTPException(status_code=409, detail="이미 가입된 이메일입니다.")

        user = self.user_repo.create(name=row.name, email=row.email, password_hash=row.password_hash)
        row.status = SignupRequestStatus.approved
        row.reviewed_by = admin_user.id
        row.reviewed_at = datetime.now(timezone.utc)
        row = self.repo.save(row)
        return row, user

    def reject(self, *, request_id: str, admin_user: User) -> SignupRequest:
        self.ensure_admin(admin_user)
        row = self.repo.get(request_id)
        if not row:
            raise HTTPException(status_code=404, detail="가입 요청을 찾을 수 없습니다.")
        if row.status != SignupRequestStatus.pending:
            raise HTTPException(status_code=409, detail="이미 처리된 가입 요청입니다.")

        row.status = SignupRequestStatus.rejected
        row.reviewed_by = admin_user.id
        row.reviewed_at = datetime.now(timezone.utc)
        return self.repo.save(row)
