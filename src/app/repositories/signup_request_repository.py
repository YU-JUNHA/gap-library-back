from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import SignupRequestStatus
from app.models.signup_request import SignupRequest


class SignupRequestRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, row: SignupRequest) -> SignupRequest:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def get(self, request_id: str) -> SignupRequest | None:
        return self.db.get(SignupRequest, request_id)

    def list_pending(self) -> list[SignupRequest]:
        stmt = select(SignupRequest).where(SignupRequest.status == SignupRequestStatus.pending).order_by(SignupRequest.requested_at.asc())
        return self.db.execute(stmt).scalars().all()

    def save(self, row: SignupRequest) -> SignupRequest:
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row
