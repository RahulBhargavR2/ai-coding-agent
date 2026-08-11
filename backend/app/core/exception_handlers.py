from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    AppException,
    BusinessValidationError,
    EmailAlreadyExists,
    ExpiredToken,
    InactiveUser,
    InvalidCredentials,
    InvalidToken,
    LLMError,
    PermissionDenied,
    RepositoryNotFound,
    UserNotFound,
    WorkspaceNotFound,
    WorkspaceAlreadyExists
)


def exception_response(
    status_code: int,
    message: str,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "detail": message,
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register application exception handlers."""

    @app.exception_handler(InvalidCredentials)
    async def invalid_credentials_handler(
        request: Request,
        exc: InvalidCredentials,
    ):
        return exception_response(
            status.HTTP_401_UNAUTHORIZED,
            exc.message,
        )

    @app.exception_handler(InvalidToken)
    async def invalid_token_handler(
        request: Request,
        exc: InvalidToken,
    ):
        return exception_response(
            status.HTTP_401_UNAUTHORIZED,
            exc.message,
        )

    @app.exception_handler(ExpiredToken)
    async def expired_token_handler(
        request: Request,
        exc: ExpiredToken,
    ):
        return exception_response(
            status.HTTP_401_UNAUTHORIZED,
            exc.message,
        )

    @app.exception_handler(InactiveUser)
    async def inactive_user_handler(
        request: Request,
        exc: InactiveUser,
    ):
        return exception_response(
            status.HTTP_403_FORBIDDEN,
            exc.message,
        )

    @app.exception_handler(PermissionDenied)
    async def permission_handler(
        request: Request,
        exc: PermissionDenied,
    ):
        return exception_response(
            status.HTTP_403_FORBIDDEN,
            exc.message,
        )

    @app.exception_handler(UserNotFound)
    async def user_not_found_handler(
        request: Request,
        exc: UserNotFound,
    ):
        return exception_response(
            status.HTTP_404_NOT_FOUND,
            exc.message,
        )

    @app.exception_handler(RepositoryNotFound)
    async def repository_not_found_handler(
        request: Request,
        exc: RepositoryNotFound,
    ):
        return exception_response(
            status.HTTP_404_NOT_FOUND,
            exc.message,
        )

    @app.exception_handler(WorkspaceNotFound)
    async def workspace_not_found_handler(
        request: Request,
        exc: WorkspaceNotFound,
    ):
        return exception_response(
            status.HTTP_404_NOT_FOUND,
            exc.message,
        )
    
    @app.exception_handler(WorkspaceAlreadyExists)
    async def workspace_already_exists_handler(
        request:Request,
        exc:WorkspaceAlreadyExists,
    ):
        return exception_response(
            status.HTTP_409_CONFLICT,
            exc.message
        )

    @app.exception_handler(EmailAlreadyExists)
    async def email_exists_handler(
        request: Request,
        exc: EmailAlreadyExists,
    ):
        return exception_response(
            status.HTTP_409_CONFLICT,
            exc.message,
        )

    @app.exception_handler(BusinessValidationError)
    async def validation_handler(
        request: Request,
        exc: BusinessValidationError,
    ):
        return exception_response(
            status.HTTP_400_BAD_REQUEST,
            exc.message,
        )

    @app.exception_handler(LLMError)
    async def llm_handler(
        request: Request,
        exc: LLMError,
    ):
        return exception_response(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            exc.message,
        )

    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request,
        exc: AppException,
    ):
        return exception_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            exc.message,
        )
