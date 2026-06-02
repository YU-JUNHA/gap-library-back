from datetime import datetime

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refreshToken: str


class LogoutRequest(BaseModel):
    refreshToken: str


class AuthUserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    organization: str | None = None
    avatarUrl: str | None = None
    createdAt: datetime
