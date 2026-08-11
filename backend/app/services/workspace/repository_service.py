from __future__ import annotations

from pathlib import Path
from uuid import UUID
from urllib.parse import urlparse

from app.models.enums import RepositoryProvider, RepositoryStatus
from app.models.repository import Repository
from app.schemas.repository import (
    GithubRepositoryCreate,
    UploadRepositoryCreate,
)
from app.dependencies.uow import UnitOfWorkDep


class RepositoryService:

    def __init__(
        self,
        uow: UnitOfWorkDep,
    ) -> None:
        self.uow = uow

    # ------------------------------------------------------------------
    # Create GitHub Repository
    # ------------------------------------------------------------------

    def create_github_repository(
        self,
        user_id: UUID,
        data: GithubRepositoryCreate,
    ) -> Repository:

        project = self.uow.projects.get_by_id_and_user(
            data.project_id,
            user_id,
        )

        if project is None:
            raise ValueError("Project not found.")

        if self.uow.repositories.exists_by_url(
            data.project_id,
            str(data.url),
        ):
            raise ValueError("Repository already registered.")

        repository = Repository(
            project_id=data.project_id,
            name=self._extract_repository_name(
                str(data.url),
            ),
            provider=RepositoryProvider.GITHUB,
            url=str(data.url),
            default_branch="main",
            current_branch="main",
            status=RepositoryStatus.PENDING,
        )

        repository = self.uow.repositories.create(
            repository,
        )

        self.uow.commit()
        self.uow.refresh(repository)

        return repository

    # ------------------------------------------------------------------
    # Create Uploaded Repository
    # ------------------------------------------------------------------

    def create_uploaded_repository(
        self,
        user_id: UUID,
        data: UploadRepositoryCreate,
    ) -> Repository:

        project = self.uow.projects.get_by_id_and_user(
            data.project_id,
            user_id,
        )

        if project is None:
            raise ValueError("Project not found.")

        if self.uow.repositories.exists_by_name(
            data.project_id,
            data.name,
        ):
            raise ValueError("Repository already exists.")

        repository = Repository(
            project_id=data.project_id,
            name=data.name,
            provider=RepositoryProvider.UPLOAD,
            url=None,
            default_branch="main",
            current_branch="main",
            status=RepositoryStatus.PENDING,
        )

        repository = self.uow.repositories.create(
            repository,
        )

        self.uow.commit()
        self.uow.refresh(repository)

        return repository

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_repository(
        self,
        repository_id: UUID,
        user_id: UUID,
    ) -> Repository:

        repository = self.uow.repositories.get_by_id_and_user(
            repository_id,
            user_id,
        )

        if repository is None:
            raise ValueError("Repository not found.")

        return repository

    def list_project_repositories(
        self,
        project_id: UUID,
        user_id: UUID,
    ) -> list[Repository]:

        project = self.uow.projects.get_by_id_and_user(
            project_id,
            user_id,
        )

        if project is None:
            raise ValueError("Project not found.")

        return self.uow.repositories.list_by_project(
            project_id,
        )

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_repository(
        self,
        repository_id: UUID,
        user_id: UUID,
    ) -> None:

        repository = self.get_repository(
            repository_id,
            user_id,
        )

        self.uow.repositories.delete(
            repository,
        )

        self.uow.commit()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_repository_name(
        url: str,
    ) -> str:
        """
        Extract the repository name from a GitHub URL.

        Example:
        https://github.com/openai/openai-python.git
        ->
        openai-python
        """

        path = Path(urlparse(url).path)

        return path.stem
