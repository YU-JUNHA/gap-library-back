from datetime import datetime

from pydantic import BaseModel, EmailStr


class SignupRequestCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    inviteCode: str | None = None


class SignupRequestOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    status: str
    requestedAt: datetime
    reviewedAt: datetime | None = None
    reviewedBy: str | None = None
