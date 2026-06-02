from fastapi import APIRouter, Depends

from app.api.deps.auth import DbSession, get_current_user
from app.models.user import User
from app.schemas.auth import AuthUserOut, LoginRequest, LogoutRequest, RefreshRequest
from app.services.auth_service import AuthService

router = APIRouter()


def to_user_out(user: User) -> AuthUserOut:
    return AuthUserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role.value,
        organization=user.organization,
        avatarUrl=user.avatar_url,
        createdAt=user.created_at,
    )


@router.post("/login")
def login(payload: LoginRequest, db: DbSession):
    access_token, refresh_token, user = AuthService(db).login(email=payload.email, password=payload.password)
    return {
        "data": {
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "user": to_user_out(user).model_dump(),
        }
    }


@router.post("/refresh")
def refresh(payload: RefreshRequest, db: DbSession):
    access_token, refresh_token = AuthService(db).refresh(refresh_token=payload.refreshToken)
    return {"data": {"accessToken": access_token, "refreshToken": refresh_token}}


@router.post("/logout")
def logout(payload: LogoutRequest, db: DbSession):
    AuthService(db).logout(refresh_token=payload.refreshToken)
    return {"data": {"success": True}}


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {"data": to_user_out(current_user).model_dump()}
