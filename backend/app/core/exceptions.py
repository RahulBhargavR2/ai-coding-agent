from __future__ import annotations

class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


# ============================================================================
# Authentication
# ============================================================================


class InvalidCredentials(AppException):
    """Raised when authentication credentials are invalid."""


class EmailAlreadyExists(AppException):
    """Raised when attempting to register an existing email."""


class InvalidToken(AppException):
    """Raised when a JWT or refresh token is invalid."""


class ExpiredToken(AppException):
    """Raised when a token has expired."""


class InactiveUser(AppException):
    """Raised when an inactive user attempts to authenticate."""


class UserNotFound(AppException):
    """Raised when the requested user does not exist."""


# ============================================================================
# Authorization
# ============================================================================


class PermissionDenied(AppException):
    """Raised when a user lacks permission."""


# ============================================================================
# Repository
# ============================================================================


class RepositoryNotFound(AppException):
    """Raised when a repository cannot be found."""


class WorkspaceNotFound(AppException):
    """Raised when a workspace cannot be found."""


class WorkspaceAlreadyExists(AppException):
    """Raised when a workspace cannot be found."""



class ProjectAlreadyExists(AppException):
    """Raise when attempting to create a Project with same name inside a workspace"""


# ============================================================================
# Validation
# ============================================================================


class BusinessValidationError(AppException):
    """Raised when business validation fails."""


# ============================================================================
# AI
# ============================================================================


class LLMError(AppException):
    """Raised when an LLM provider fails."""
