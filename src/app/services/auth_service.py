from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_token, verify_password
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.refresh_repo = RefreshTokenRepository(db)

    def login(self, *, email: str, password: str) -> tuple[str, str, User]:
        user = self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
        self.user_repo.touch_last_login(user, datetime.now(timezone.utc))

        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
        self.refresh_repo.create(user_id=user.id, token=refresh_token, expires_at=expires_at)
        return access_token, refresh_token, user

    def refresh(self, *, refresh_token: str) -> tuple[str, str]:
        row = self.refresh_repo.get_by_token(refresh_token)
        if not row or row.revoked:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 refresh token 입니다.")
        if row.expires_at < datetime.now(timezone.utc):
            self.refresh_repo.revoke(row)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="만료된 refresh token 입니다.")

        try:
            payload = decode_token(refresh_token)
        except ValueError as exc:
            self.refresh_repo.revoke(row)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 refresh token 입니다.") from exc

        if payload.get("type") != "refresh" or payload.get("sub") != row.user_id:
            self.refresh_repo.revoke(row)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 refresh token 입니다.")

        self.refresh_repo.revoke(row)
        new_access = create_access_token(row.user_id)
        new_refresh = create_refresh_token(row.user_id)
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
        self.refresh_repo.create(user_id=row.user_id, token=new_refresh, expires_at=expires_at)
        return new_access, new_refresh

    def logout(self, *, refresh_token: str) -> None:
        row = self.refresh_repo.get_by_token(refresh_token)
        if row and not row.revoked:
            self.refresh_repo.revoke(row)

    def get_current_user_from_access_token(self, token: str) -> User:
        try:
            payload = decode_token(token)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 access token 입니다.") from exc

        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 access token 입니다.")

        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 access token 입니다.")

        user = self.user_repo.get_by_id(sub)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="사용자를 찾을 수 없습니다.")
        return user
