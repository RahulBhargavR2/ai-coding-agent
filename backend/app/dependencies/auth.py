from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import (
    PermissionDenied,
    InactiveUser,
    InvalidCredentials,
    InvalidToken,
)
from app.dependencies.database import DBSession
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.auth.jwt_service import JWTService

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(security),
    ],
    db: DBSession,
) -> User:
    """
    Retrieve the currently authenticated user.
    """

    if credentials is None:
        raise InvalidCredentials("Authentication credentials were not provided.")

    jwt_service = JWTService()

    token = credentials.credentials

    user_id = jwt_service.get_subjects(token)

    try:
        user_uuid = UUID(user_id)
    except ValueError as exc:
        raise InvalidToken("Invalid token subject.") from exc

    repository = UserRepository(db)

    user = repository.get_by_id(user_uuid)

    if user is None:
        raise InvalidCredentials("User not found.")

    return user


def get_current_active_user(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> User:
    """
    Ensure the authenticated user is active.
    """

    if not current_user.is_active:
        raise InactiveUser("Inactive user.")

    return current_user


def get_current_admin(
    current_user: Annotated[
        User,
        Depends(get_current_active_user),
    ],
) -> User:
    """
    Ensure the authenticated user is an administrator.
    """

    if current_user.role != UserRole.ADMIN:
        raise PermissionDenied("You do not have permission to perform this action.")

    return current_user


CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]

CurrentActiveUser = Annotated[
    User,
    Depends(get_current_active_user),
]

CurrentAdmin = Annotated[
    User,
    Depends(get_current_admin),
]
