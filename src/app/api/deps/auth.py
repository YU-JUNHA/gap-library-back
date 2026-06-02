from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import AuthService


DbSession = Annotated[Session, Depends(get_db)]
bearer_scheme = HTTPBearer()


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> User:
    return AuthService(db).get_current_user_from_access_token(credentials.credentials)
