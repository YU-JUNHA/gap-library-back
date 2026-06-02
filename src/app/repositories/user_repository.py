from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.sentinels import UNSET
from app.core.security import get_password_hash
from app.models.enums import UserRole
from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: str) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.execute(select(User).where(User.email == email)).scalar_one_or_none()

    def get_first(self) -> User | None:
        return self.db.execute(select(User).order_by(User.created_at.asc())).scalar_one_or_none()

    def create(self, *, name: str, email: str, password_hash: str, organization: str | None = None) -> User:
        user = User(name=name, email=email, password_hash=password_hash, organization=organization)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def touch_last_login(self, user: User, at: datetime) -> User:
        user.last_login_at = at
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def list_users(self, *, q: str | None, role: str | None, page: int, page_size: int) -> tuple[list[User], int]:
        stmt = select(User)
        count_stmt = select(func.count(User.id))

        if q:
            like_q = f"%{q}%"
            stmt = stmt.where(User.name.ilike(like_q) | User.email.ilike(like_q))
            count_stmt = count_stmt.where(User.name.ilike(like_q) | User.email.ilike(like_q))
        if role:
            stmt = stmt.where(User.role == role)
            count_stmt = count_stmt.where(User.role == role)

        stmt = stmt.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        rows = self.db.execute(stmt).scalars().all()
        total = self.db.execute(count_stmt).scalar_one()
        return rows, total

    def count_admins(self) -> int:
        return self.db.execute(select(func.count(User.id)).where(User.role == UserRole.admin)).scalar_one()

    def update_role(self, user: User, role: UserRole) -> User:
        user.role = role
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_me(
        self,
        user: User,
        *,
        name: str | None,
        organization: str | None,
        avatar_url: str | None | object = UNSET,
    ) -> User:
        if name is not None:
            user.name = name
        if organization is not None:
            user.organization = organization
        if avatar_url is not UNSET:
            user.avatar_url = avatar_url

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_password(self, user: User, new_password: str) -> User:
        user.password_hash = get_password_hash(new_password)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
