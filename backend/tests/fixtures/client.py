import pytest

from fastapi.testclient import TestClient

from app.database.session import get_db
from app.main import app


@pytest.fixture(scope='function')
def client(db_session):
    """
    Returns a FastAPI TestClient that uses
    the test database session.
    """

    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db,None)
