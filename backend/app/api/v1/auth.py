from fastapi import APIRouter, status

from app.dependencies import DBSession
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
)
from app.services.auth.auth_service import AuthService

from app.dependencies.auth import CurrentUser
from app.dependencies.uow import UnitOfWorkDep

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: RegisterRequest,
    uow:UnitOfWorkDep
) -> RegisterResponse:
    """
    Register a new user.
    """
    service = AuthService(uow)
    return service.register(request)


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
)
def login(
    request: LoginRequest,
    uow:UnitOfWorkDep
) -> LoginResponse:
    """
    Authenticate a user.
    """
    service = AuthService(uow)
    return service.login(request)


@router.post(
    "/refresh",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
)
def refresh(
    request: RefreshTokenRequest,
    uow:UnitOfWorkDep
) -> LoginResponse:
    """
    Generate a new access token using a refresh token.
    """
    service = AuthService(uow)
    return service.refresh(request)


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
def logout(
    request: LogoutRequest,
    uow:UnitOfWorkDep
) -> MessageResponse:
    """
    Logout the current device.
    """
    service = AuthService(uow)
    service.logout(request)

    return MessageResponse(message="Logged out successfully.")


@router.get("/me")
def me(
    current_user: CurrentUser,
):
    return current_user
