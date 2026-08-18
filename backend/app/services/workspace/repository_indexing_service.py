from __future__ import annotations

from pathlib import Path
from uuid import UUID

from app.core.exceptions import RepositoryNotFound
from app.dependencies.uow import UnitOfWorkDep
from app.indexing.pipeline import IndexingPipeline, IndexingResult
from app.models.repository import Repository
from app.services.workspace.repository_service import RepositoryService


class RepositoryIndexingService:
    """
    Coordinates repository indexing operations.

    This service is responsible for:
    - validating repository ownership,
    - invoking the indexing pipeline,
    - exposing indexing operations to the API layer.

    The actual indexing workflow is implemented by IndexingPipeline.
    """

    def __init__(
        self,
        uow: UnitOfWorkDep,
        pipeline: IndexingPipeline,
    ) -> None:
        self.uow = uow
        self.pipeline = pipeline

    def index_repository(
        self,
        repository_id: UUID,
        user_id: UUID,
        *,
        archive_path: Path | None = None,
        source_path: Path | None = None,
    ) -> IndexingResult:
        """
        Import and index a repository owned by the current user.
        """

        repository = self.uow.repositories.get_by_id_and_user(
            repository_id=repository_id,
            user_id=user_id,
        )

        if repository is None:
            raise RepositoryNotFound(f"Repository {repository_id} not found.")

        return self.pipeline.run(
            repository=repository,
            archive_path=archive_path,
            source_path=source_path,
        )
