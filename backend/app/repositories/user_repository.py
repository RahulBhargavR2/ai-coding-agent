from __future__ import annotations

from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model."""

    def __init__(self, db: Session):
        super().__init__(db, User)

    def create(
        self,
        user: User
    ):

        return self._persist(user)

    def get_by_id(self, id:UUID) -> User | None:
        stmt = select(User).where(User.id == id)

        return self.db.scalar(stmt)

    def get_by_email(self, email: str) -> User | None:
        """Retrieve a user by email."""

        stmt = select(User).where(User.email == email)
        return self.db.scalar(stmt)

    def exists_by_email(self, email: str) -> bool:
        """Check whether a user exists by email."""

        stmt = select(User.id).where(User.email == email)
        return self.db.scalar(stmt) is not None

    def get_active_user(self, email: str) -> User | None:
        """Retrieve an active user by email."""

        stmt = select(User).where(
            User.email == email,
            User.is_active.is_(True),
        )

        return self.db.scalar(stmt)
