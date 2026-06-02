from fastapi import APIRouter

from app.api.deps.auth import DbSession
from app.schemas.signup_request import SignupRequestCreate
from app.services.signup_request_service import SignupRequestService

router = APIRouter()


@router.post("")
def create_signup_request(payload: SignupRequestCreate, db: DbSession):
    row = SignupRequestService(db).create_request(
        name=payload.name,
        email=payload.email,
        password=payload.password,
        invite_code=payload.inviteCode,
    )
    return {
        "data": {
            "id": row.id,
            "name": row.name,
            "email": row.email,
            "status": row.status.value,
            "requestedAt": row.requested_at,
        }
    }
