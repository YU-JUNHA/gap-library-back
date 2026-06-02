from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: EmailStr
    role: str
    organization: str | None = None
    avatarUrl: str | None = None
    createdAt: datetime


class UserMeUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    organization: str | None = None
    avatarUrl: str | None = None


class UserAvatarUploadOut(BaseModel):
    avatarUrl: str


class UserPasswordUpdate(BaseModel):
    currentPassword: str
    newPassword: str
