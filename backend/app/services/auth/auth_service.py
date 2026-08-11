from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import (
    InvalidCredentials,
    EmailAlreadyExists,
    InvalidToken,
    ExpiredToken,
    UserNotFound,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
)
from app.schemas.user import UserResponse
from app.services.auth.jwt_service import JWTService
from app.services.auth.password_service import PasswordService
from app.services.auth.token_service import TokenService
from app.dependencies.uow import UnitOfWorkDep


class AuthService:
    """Service responsible for authentication workflows."""

    def __init__(self, uow:UnitOfWorkDep):
        self.uow = uow

        self.password_service = PasswordService()
        self.jwt_service = JWTService()
        self.token_service = TokenService()

    def register(self, request: RegisterRequest) -> RegisterResponse:
        """
        Register a new user.
        """

        if self.uow.users.exists_by_email(request.email):
            raise EmailAlreadyExists("A user with this email already exists.")

        user = User(
            name=request.name,
            email=request.email,
            hashed_password=self.password_service.hash_password(request.password),
        )

        try:
            self.uow.users.create(user)

            self.uow.commit()
            self.uow.refresh(user)

        except Exception:
            self.uow.rollback()
            raise

        return RegisterResponse(
            message="User registered successfully.",
            user=UserResponse.model_validate(user),
        )

    def login(self, request: LoginRequest) -> LoginResponse:
        """
        Authenticate a user.
        """

        user = self.uow.users.get_by_email(request.email)

        if user is None:
            raise InvalidCredentials("Invalid email or password")

        if not self.password_service.verify_password(
            request.password,
            user.hashed_password,
        ):
            raise InvalidCredentials("Invalid email or password.")

        access_token = self.jwt_service.create_access_token(subject=str(user.id))

        refresh_token = self.token_service.generate_refresh_token()

        refresh_token_model = RefreshToken(
            user_id=user.id,
            token_hash=self.token_service.hash_token(refresh_token),
            expires_at=self.token_service.get_expiration(),
        )

        try:
            self.uow.refresh_tokens.create(refresh_token_model)

            self.uow.commit()

        except Exception:
            self.uow.rollback()
            raise

        return LoginResponse(
            user=UserResponse.model_validate(user),
            access_token=access_token,
            refresh_token=refresh_token,
        )

    def refresh(
        self,
        request: RefreshTokenRequest,
    ) -> LoginResponse:
        """
        Rotate a refresh token and issue a new access token.
        """

        token_hash = self.token_service.hash_token(request.refresh_token)

        stored_token = self.uow.refresh_tokens.get_active_token(token_hash)

        if stored_token is None:
            raise InvalidToken("Invalid or expired refresh token.")

        user = stored_token.user

        access_token = self.jwt_service.create_access_token(subject=str(user.id))

        new_refresh_token = self.token_service.generate_refresh_token()

        new_refresh_model = RefreshToken(
            user_id=user.id,
            token_hash=self.token_service.hash_token(new_refresh_token),
            expires_at=self.token_service.get_expiration(),
        )

        try:
            self.uow.refresh_tokens.revoke(stored_token)

            self.uow.refresh_tokens.create(new_refresh_model)

            self.uow.commit()

        except Exception:
            self.uow.rollback()
            raise

        return LoginResponse(
            user=UserResponse.model_validate(user),
            access_token=access_token,
            refresh_token=new_refresh_token,
        )

    def logout(self, request: LogoutRequest) -> None:
        """
        Logout a user by revoking the refresh token.
        """

        token_hash = self.token_service.hash_token(request.refresh_token)

        stored_token = self.uow.refresh_tokens.get_by_token_hash(token_hash)

        if stored_token is None:
            raise InvalidToken("Invalid refresh token.")

        try:
            self.uow.refresh_tokens.revoke(stored_token)

            self.uow.commit()

        except Exception:
            self.uow.rollback()
            raise


