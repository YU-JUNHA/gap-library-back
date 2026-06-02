import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.core.security import get_password_hash
from app.main import app
from app.db.session import SessionLocal, Base
from app.models.enums import UserRole
from app.models.user import User


@pytest.fixture()
def db_session():
    db = SessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(delete(table))
        db.commit()
        yield db
    finally:
        db.close()


@pytest.fixture()
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


def create_user(db, *, email: str, password: str, role: UserRole = UserRole.member, name: str = "User") -> User:
    user = User(
        id=str(uuid.uuid4()),
        name=name,
        email=email,
        password_hash=get_password_hash(password),
        role=role,
        organization="GAP",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


async def login(client: AsyncClient, email: str, password: str) -> dict:
    res = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["data"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
