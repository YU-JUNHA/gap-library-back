from __future__ import annotations

import logging

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.enums import UserRole
from app.models.user import User


logger = logging.getLogger(__name__)


class BootstrapService:
    def __init__(self, db: Session):
        self.db = db

    def seed_initial_data(self) -> None:
        bind = self.db.get_bind()
        if bind is None:
            logger.warning("No database bind available. Skipping initial data seed.")
            return

        inspector = inspect(bind)
        if not inspector.has_table("users"):
            logger.warning("Users table does not exist yet. Skipping initial data seed.")
            return

        if self.db.query(User).filter(User.email == "qetu5702@gmail.com").first():
            logger.info("Initial admin user already exists. Skipping seed.")
            return

        user = User(
            name="유준하",
            email="qetu5702@gmail.com",
            password_hash=get_password_hash("dbwnsgk7575*"),
            role=UserRole.admin,
            organization="GAP",
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        logger.info("Initial admin user seeded: %s", user.email)
