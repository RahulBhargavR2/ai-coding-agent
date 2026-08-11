import pytest

from app.services.auth.password_service import PasswordService
from app.services.auth.token_service import TokenService

@pytest.fixture(scope="session")
def password_service():
    """
    Production password service.
    """
    return PasswordService()


@pytest.fixture(scope='session')
def token_service():
    return TokenService()

