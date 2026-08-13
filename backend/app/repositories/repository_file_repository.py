from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.repository import Repository
from app.models.repository_file import RepositoryFile
from app.models.workspace import Workspace
from app.repositories.base_repository import BaseRepository


class RepositoryFileRepository(BaseRepository[RepositoryFile]):
    """
    Handles persistence operations for repository files.
    """

    def __init__(self, db: Session) -> None:
        super().__init__(db, RepositoryFile)

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create(
        self,
        repository_file: RepositoryFile,
    ) -> RepositoryFile:
        """
        Persist a new repository file.
        """
        return self._persist(repository_file)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_id(
        self,
        file_id: UUID,
    ) -> RepositoryFile | None:
        """
        Retrieve a repository file by its ID.
        """
        stmt = select(self.model).where(self.model.id == file_id)

        return self._first(stmt)

    def get_by_id_and_user(
        self,
        file_id: UUID,
        user_id: UUID,
    ) -> RepositoryFile | None:
        """
        Retrieve a repository file only if its repository
        belongs to a project owned by the given user.
        """

        stmt = (
            select(self.model)
            .join(Repository)
            .join(Project)
            .join(Workspace)
            .where(
                self.model.id == file_id,
                Workspace.user_id == user_id,
            )
        )

        return self._first(stmt)

    def list_by_repository(
        self,
        repository_id: UUID,
    ) -> list[RepositoryFile]:
        """
        Retrieve all files belonging to a repository.
        """

        stmt = (
            select(self.model)
            .where(
                self.model.repository_id == repository_id,
            )
            .order_by(self.model.relative_path.asc())
        )

        return self._scalars(stmt).all()

    # ------------------------------------------------------------------
    # Existence
    # ------------------------------------------------------------------

    def exists_by_path(
        self,
        repository_id: UUID,
        relative_path: str,
    ) -> bool:
        """
        Check whether a file already exists at the given
        path inside a repository.
        """

        stmt = (
            select(self.model.id)
            .where(
                self.model.repository_id == repository_id,
                self.model.relative_path == relative_path,
            )
            .limit(1)
        )

        return self._scalar(stmt) is not None

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def list_by_indexed_status(
        self,
        repository_id: UUID,
        is_indexed: bool,
    ) -> list[RepositoryFile]:
        """
        Retrieve repository files according to their indexing status.
        """

        stmt = (
            select(self.model)
            .where(
                self.model.repository_id == repository_id,
                self.model.is_indexed == is_indexed,
            )
            .order_by(self.model.relative_path.asc())
        )

        return self._scalars(stmt).all()

    def list_pending_indexing(
        self,
        repository_id: UUID,
    ) -> list[RepositoryFile]:
        """
        Retrieve files that have not yet been indexed.
        """

        return self.list_by_indexed_status(
            repository_id=repository_id,
            is_indexed=False,
        )

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete(
        self,
        repository_file: RepositoryFile,
    ) -> None:
        """
        Delete a repository file.
        """
        super().delete(repository_file)
