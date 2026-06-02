from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, *, user_id: str, token: str, expires_at: datetime) -> RefreshToken:
        row = RefreshToken(user_id=user_id, token=token, expires_at=expires_at, revoked=False)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def get_by_token(self, token: str) -> RefreshToken | None:
        return self.db.execute(select(RefreshToken).where(RefreshToken.token == token)).scalar_one_or_none()

    def revoke(self, row: RefreshToken) -> RefreshToken:
        row.revoked = True
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row
