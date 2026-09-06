import pytest
from uuid import UUID

from app.models.enums import RepositoryProvider, RepositoryStatus
from app.models.repository import Repository


@pytest.fixture
def repository_factory(db_session, project):
    """
    Factory for creating Repository instances.
    """

    def factory(
        *,
        project_id: UUID | None = None,
        name: str = "Test Repository",
        provider: RepositoryProvider = RepositoryProvider.LOCAL,
        url: str | None = None,
        default_branch: str = "main",
        current_branch: str = "main",
        commit_hash: str | None = None,
        local_path: str | None = None,
        status: RepositoryStatus = RepositoryStatus.PENDING,
    ) -> Repository:
        repository = Repository(
            project_id=(project.id if project_id is None else project_id),
            name=name,
            provider=provider,
            url=url,
            default_branch=default_branch,
            current_branch=current_branch,
            commit_hash=commit_hash,
            local_path=local_path,
            status=status,
        )

        db_session.add(repository)
        db_session.flush()

        return repository

    return factory


@pytest.fixture
def repository(repository_factory):
    return repository_factory()
