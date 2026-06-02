from fastapi import APIRouter, Depends, File, UploadFile

from app.core.sentinels import UNSET
from app.api.deps.auth import DbSession, get_current_user
from app.models.user import User
from app.schemas.user import UserAvatarUploadOut, UserMeUpdate, UserOut, UserPasswordUpdate
from app.core.config import settings
from app.services.file_storage import LocalFileStorage
from app.services.user_service import UserService

router = APIRouter()


def to_user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role.value,
        organization=user.organization,
        avatarUrl=user.avatar_url,
        createdAt=user.created_at,
    )


@router.get("/me")
def get_me(db: DbSession, current_user: User = Depends(get_current_user)):
    user = UserService(db).get_me(current_user)
    return {"data": to_user_out(user).model_dump()}


@router.patch("/me")
def patch_me(payload: UserMeUpdate, db: DbSession, current_user: User = Depends(get_current_user)):
    update_data = payload.model_dump(exclude_unset=True)
    user = UserService(db).update_me(
        current_user,
        name=update_data.get("name"),
        organization=update_data.get("organization"),
        avatar_url=update_data.get("avatarUrl", UNSET),
    )
    return {"data": to_user_out(user).model_dump()}


@router.post("/me/avatar")
async def upload_avatar(
    db: DbSession,
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(...),
):
    storage = LocalFileStorage(settings.file_storage_root, settings.file_public_prefix)
    storage.ensure_root()
    avatar_url = await storage.save_avatar(user_id=current_user.id, file=file)
    user = UserService(db).update_me(current_user, name=None, organization=None, avatar_url=avatar_url)
    return {"data": UserAvatarUploadOut(avatarUrl=user.avatar_url).model_dump()}


@router.patch("/me/password")
def patch_me_password(
    payload: UserPasswordUpdate,
    db: DbSession,
    current_user: User = Depends(get_current_user),
):
    UserService(db).update_password(
        current_user,
        current_password=payload.currentPassword,
        new_password=payload.newPassword,
    )
    return {"data": {"success": True}}
