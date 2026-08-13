from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID

from app.core.exceptions import (
    ProjectNotFound,
    RepositoryAlreadyExists,
    RepositoryNotFound,
    BusinessValidationError
)
from app.models.enums import RepositoryProvider, RepositoryStatus
from app.models.repository import Repository
from app.schemas.repository import (
    GithubRepositoryCreate,
    UploadRepositoryCreate,
)
from app.dependencies.uow import UnitOfWork


class RepositoryService:
    """
    Handles repository metadata and lifecycle operations.

    Actual cloning, file discovery, parsing, chunking, and indexing
    are handled by separate services in later stages.
    """

    def __init__(
        self,
        uow: UnitOfWork,
    ) -> None:
        self.uow = uow

    # ------------------------------------------------------------------
    # GitHub
    # ------------------------------------------------------------------

    def create_github_repository(
        self,
        user_id: UUID,
        data: GithubRepositoryCreate,
    ) -> Repository:
        """
        Register a GitHub repository with a project.
        """

        project = self.uow.projects.get_by_id_and_user(
            project_id=data.project_id,
            user_id=user_id,
        )

        if project is None:
            raise ProjectNotFound(f"Project {data.project_id} not found.")

        repository_url = str(data.url)

        if self.uow.repositories.exists_by_url(
            project_id=data.project_id,
            url=repository_url,
        ):
            raise RepositoryAlreadyExists(
                "A repository with this URL is already registered."
            )

        repository = Repository(
            project_id=data.project_id,
            name=self._extract_repository_name(repository_url),
            provider=RepositoryProvider.GITHUB,
            url=repository_url,
            default_branch="main",
            current_branch="main",
            status=RepositoryStatus.PENDING,
        )

        repository = self.uow.repositories.create(repository)

        self.uow.commit()
        self.uow.refresh(repository)

        return repository

    # ------------------------------------------------------------------
    # Upload
    # ------------------------------------------------------------------

    def create_uploaded_repository(
        self,
        user_id: UUID,
        data: UploadRepositoryCreate,
    ) -> Repository:
        """
        Register an uploaded repository.

        Actual file extraction and scanning are handled later.
        """

        project = self.uow.projects.get_by_id_and_user(
            project_id=data.project_id,
            user_id=user_id,
        )

        if project is None:
            raise ProjectNotFound(f"Project {data.project_id} not found.")

        if self.uow.repositories.exists_by_name(
            project_id=data.project_id,
            name=data.name,
        ):
            raise RepositoryAlreadyExists(
                f"Repository '{data.name}' already exists "
                f"in project {data.project_id}."
            )

        repository = Repository(
            project_id=data.project_id,
            name=data.name,
            provider=RepositoryProvider.UPLOAD,
            url=None,
            default_branch="main",
            current_branch="main",
            status=RepositoryStatus.PENDING,
        )

        repository = self.uow.repositories.create(repository)

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
        """
        Retrieve a repository owned by the current user.
        """

        repository = self.uow.repositories.get_by_id_and_user(
            repository_id=repository_id,
            user_id=user_id,
        )

        if repository is None:
            raise RepositoryNotFound(f"Repository {repository_id} not found.")

        return repository

    def list_project_repositories(
        self,
        project_id: UUID,
        user_id: UUID,
    ) -> list[Repository]:
        """
        List repositories belonging to a project owned by the user.
        """

        project = self.uow.projects.get_by_id_and_user(
            project_id=project_id,
            user_id=user_id,
        )

        if project is None:
            raise ProjectNotFound(f"Project {project_id} not found.")

        return self.uow.repositories.list_by_project(
            project_id=project_id,
        )

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_repository(
        self,
        repository_id: UUID,
        user_id: UUID,
    ) -> None:
        """
        Delete repository metadata.

        Physical repository data and indexing artifacts will be
        handled by the ingestion/indexing layer later.
        """

        repository = self.get_repository(
            repository_id=repository_id,
            user_id=user_id,
        )

        self.uow.repositories.delete(repository)
        self.uow.commit()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_repository_name(url: str) -> str:
        """
        Extract repository name from a remote URL.

        Example:
            https://github.com/openai/openai-python.git
            -> openai-python
        """

        path = urlparse(url).path.rstrip("/")

        name = Path(path).name

        if name.endswith(".git"):
            name = name[:-4]

        if not name:
            raise BusinessValidationError("Unable to determine repository name.")

        return name
