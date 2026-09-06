from uuid import uuid4

import pytest

from app.models.enums import UserRole
from app.models.user import User


@pytest.fixture
def user_factory(db_session, password_service):
    """
    Factory for creating users.
    """

    def factory(
        *,
        name="Test User",
        email=None,
        password="CorrectPassword123!",
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
    ):
        user = User(
            name=name,
            email=email or f"{uuid4()}@example.com",
            hashed_password=password_service.hash_password(password),
            role=role,
            is_active=is_active,
            is_verified=is_verified,
        )

        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        return user

    return factory


@pytest.fixture
def user(user_factory):
    """
    Standard authenticated user.
    """
    return user_factory()
