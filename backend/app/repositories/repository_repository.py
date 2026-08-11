from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.repository import Repository
from app.models.workspace import Workspace
from app.models.enums import RepositoryStatus
from app.repositories.base_repository import BaseRepository


class RepositoryRepository(BaseRepository[Repository]):

    def __init__(self, db: Session) -> None:
        super().__init__(db, Repository)

    def create(
        self,
        repository: Repository,
    ) -> Repository:
        """
        Persist a new repository.
        """
        return self._persist(repository)

    def get_by_id_and_user(
        self,
        repository_id: UUID,
        user_id: UUID,
    ) -> Repository | None:
        """
        Retrieve a repository owned by the given user.
        """

        stmt = (
            select(self.model)
            .join(Project)
            .join(Workspace)
            .where(
                self.model.id == repository_id,
                Workspace.user_id == user_id,
            )
        )

        return self._first(stmt)

    def list_by_project(
        self,
        project_id: UUID,
    ) -> list[Repository]:
        """
        List all repositories belonging to a project.
        """

        stmt = (
            select(self.model)
            .where(
                self.model.project_id == project_id,
            )
            .order_by(self.model.updated_at.desc())
        )

        return self._scalars(stmt).all()

    def exists_by_name(
        self,
        project_id: UUID,
        name: str,
    ) -> bool:
        """
        Check whether a repository with the given name
        already exists inside the project.
        """

        stmt = (
            select(self.model.id)
            .where(
                self.model.project_id == project_id,
                func.lower(self.model.name) == name.lower(),
            )
            .limit(1)
        )

        return self._scalar(stmt) is not None

    def exists_by_url(
        self,
        project_id: UUID,
        url: str,
    ) -> bool:
        """
        Check if a Git repository has already been registered.
        """

        stmt = (
            select(self.model.id)
            .where(
                self.model.project_id == project_id,
                self.model.url == url,
            )
            .limit(1)
        )

        return self._scalar(stmt) is not None

    def list_by_status(
        self,
        status: RepositoryStatus,
    ) -> list[Repository]:
        """
        Retrieve repositories with a specific status.
        """

        stmt = (
            select(self.model)
            .where(
                self.model.status == status,
            )
            .order_by(self.model.created_at.asc())
        )

        return self._scalars(stmt).all()

    def update_status(
        self,
        repository: Repository,
        status: RepositoryStatus,
    ) -> Repository:
        """
        Update the repository status.
        """

        repository.status = status

        return repository
