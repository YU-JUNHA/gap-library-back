from pydantic import BaseModel


class AdminUserRoleUpdate(BaseModel):
    role: str
