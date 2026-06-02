from sqlalchemy.orm import Session

from app.core.sentinels import UNSET
from app.core.security import verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from fastapi import HTTPException, status


class UserService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def get_me(self, current_user: User) -> User:
        return current_user

    def update_me(
        self,
        current_user: User,
        *,
        name: str | None,
        organization: str | None,
        avatar_url: str | None | object = UNSET,
    ) -> User:
        return self.repo.update_me(
            current_user,
            name=name,
            organization=organization,
            avatar_url=avatar_url,
        )

    def update_password(self, current_user: User, *, current_password: str, new_password: str) -> User:
        if not verify_password(current_password, current_user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="현재 비밀번호가 올바르지 않습니다.")

        if len(new_password) < 8:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="새 비밀번호 형식이 올바르지 않습니다.")

        if current_password == new_password:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="새 비밀번호 형식이 올바르지 않습니다.")

        return self.repo.update_password(current_user, new_password)
