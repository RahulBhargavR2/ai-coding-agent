from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import Select
from sqlalchemy.engine import ScalarResult
from sqlalchemy.orm import Session

from app.models.base_model import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """
    Base repository providing common SQLAlchemy operations.

    This class intentionally does NOT expose generic CRUD methods such as
    get_by_id() or get_all() to enforce ownership-aware querying in
    concrete repositories.
    """

    def __init__(
        self,
        db: Session,
        model: type[ModelType],
    ) -> None:
        self._db = db
        self._model = model

    @property
    def db(self) -> Session:
        return self._db

    @property
    def model(self) -> type[ModelType]:
        return self._model

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def add(self, entity: ModelType) -> ModelType:
        self._db.add(entity)
        return entity

    def delete(self, entity: ModelType) -> None:
        self._db.delete(entity)

    def flush(self) -> None:
        self._db.flush()

    def refresh(self, entity: ModelType) -> None:
        self._db.refresh(entity)


    def _persist(
        self,
        entity: ModelType
    ) -> ModelType:
        self.add(entity)
        self.flush()
        self.refresh(entity)

        return entity

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def _scalar(self, stmt: Select):
        return self._db.scalar(stmt)

    def _scalars(self, stmt: Select) -> ScalarResult:
        return self._db.scalars(stmt)

    def _execute(self, stmt):
        return self._db.execute(stmt)

    def _first(self, stmt: Select) -> ModelType | None:
        return self._scalars(stmt).first()