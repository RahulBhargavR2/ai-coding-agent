from __future__ import annotations

from functools import cached_property

from sqlalchemy.orm import Session

from app.repositories.user_repository import UserRepository 
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.repository_repository import RepositoryRepository



class UnitOfWork:
    """
    Coordinates repositories and transaction management.

    Services should depend on UnitOfWork rather than individual repositories
    or the SQLAlchemy session.
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Repositories
    # ------------------------------------------------------------------

    @cached_property
    def users(self) -> UserRepository:
        return UserRepository(self._db)

    @cached_property
    def refresh_tokens(self) -> RefreshTokenRepository:
        return RefreshTokenRepository(self._db)
    
    @cached_property
    def workspaces(self) -> WorkspaceRepository:
        return WorkspaceRepository(self._db)

    @cached_property
    def projects(self) -> ProjectRepository:
        return ProjectRepository(self._db)

    @cached_property
    def repositories(self) -> RepositoryRepository:
        return RepositoryRepository(self._db)

    # ------------------------------------------------------------------
    # Transaction Management
    # ------------------------------------------------------------------

    def commit(self) -> None:
        self._db.commit()

    def rollback(self) -> None:
        self._db.rollback()

    def refresh(self, entity: object) -> None:
        self._db.refresh(entity)

    def commit_and_refresh(self, entity: object) -> None:
        self.commit()
        self.refresh(entity)
