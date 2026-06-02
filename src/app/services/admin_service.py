from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AdminService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    @staticmethod
    def ensure_admin(user: User) -> None:
        if user.role != UserRole.admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="관리자 권한이 필요합니다.")

    def list_users(self, *, q: str | None, role: str | None, page: int, page_size: int, admin_user: User) -> tuple[list[User], int]:
        self.ensure_admin(admin_user)
        return self.repo.list_users(q=q, role=role, page=page, page_size=page_size)

    def update_user_role(self, *, user_id: str, role: str, admin_user: User) -> User:
        self.ensure_admin(admin_user)

        target = self.repo.get_by_id(user_id)
        if not target:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

        try:
            new_role = UserRole(role)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="유효하지 않은 role 입니다.") from exc

        if target.id == admin_user.id and target.role == UserRole.admin and new_role != UserRole.admin:
            raise HTTPException(status_code=409, detail="본인 admin 계정은 강등할 수 없습니다.")

        if target.role == UserRole.admin and new_role != UserRole.admin:
            admin_count = self.repo.count_admins()
            if admin_count <= 1:
                raise HTTPException(status_code=409, detail="마지막 admin은 강등할 수 없습니다.")

        return self.repo.update_role(target, new_role)
