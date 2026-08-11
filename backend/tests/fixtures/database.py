import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session,sessionmaker

from app.database.base import Base
from app.core.config import settings


test_engine = create_engine(
    settings.TEST_DATABASE_URL,
    pool_pre_ping=True,
    echo=False
)

TestSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session
)

@pytest.fixture(scope='session')
def db_engine():
    """
    Create all tables once before the test session and 
    drop them after all tests complete
    """
    Base.metadata.create_all(bind=test_engine)

    yield test_engine

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope='function')
def db_session(db_engine):
    """Provide a clean database session for each test"""

    connection = db_engine.connect()

    transaction = connection.begin()

    session = TestSessionLocal(bind=connection)

    try:

        yield session
    finally:

        session.close()

        transaction.rollback()

        connection.close()
