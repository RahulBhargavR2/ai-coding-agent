from collections.abc import Generator

from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    echo=False,
)

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    """Provide a transactional database session."""

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Verify database connectivity."""

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        logger.success("Database connection established.")

    except Exception:
        logger.exception("Failed to connect to the database.")
        raise
