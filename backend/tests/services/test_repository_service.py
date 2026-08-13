from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.core.exceptions import (
    ProjectNotFound,
    RepositoryAlreadyExists,
    RepositoryNotFound,
)
from app.models.enums import RepositoryProvider, RepositoryStatus
from app.models.project import Project
from app.models.repository import Repository
from app.schemas.repository import (
    GithubRepositoryCreate,
    UploadRepositoryCreate,
)
from app.services.workspace.repository_service import RepositoryService


@pytest.fixture
def repository_uow():
    uow = Mock()

    uow.projects = Mock()
    uow.repositories = Mock()

    return uow


@pytest.fixture
def repository_service(repository_uow):
    return RepositoryService(repository_uow)


def test_create_github_repository_success(
    repository_service,
    repository_uow,
):
    user_id = uuid4()
    project_id = uuid4()

    project = Project(
        workspace_id=uuid4(),
        name="Project",
    )
    project.id = project_id

    request = GithubRepositoryCreate(
        project_id=project_id,
        url="https://github.com/openai/test-repository.git",
    )

    repository = Repository(
        project_id=project_id,
        name="test-repository",
        provider=RepositoryProvider.GITHUB,
        url=str(request.url),
        default_branch="main",
        current_branch="main",
        status=RepositoryStatus.PENDING,
    )

    repository_uow.projects.get_by_id_and_user.return_value = project
    repository_uow.repositories.exists_by_url.return_value = False
    repository_uow.repositories.create.return_value = repository

    result = repository_service.create_github_repository(
        user_id=user_id,
        data=request,
    )

    repository_uow.projects.get_by_id_and_user.assert_called_once_with(
        project_id=project_id,
        user_id=user_id,
    )

    repository_uow.repositories.exists_by_url.assert_called_once_with(
        project_id=project_id,
        url=str(request.url),
    )

    repository_uow.repositories.create.assert_called_once()

    repository_uow.commit.assert_called_once()
    repository_uow.refresh.assert_called_once_with(repository)

    assert result is repository


def test_create_github_repository_project_not_found(
    repository_service,
    repository_uow,
):
    repository_uow.projects.get_by_id_and_user.return_value = None

    request = GithubRepositoryCreate(
        project_id=uuid4(),
        url="https://github.com/openai/test-repository.git",
    )

    with pytest.raises(ProjectNotFound):
        repository_service.create_github_repository(
            user_id=uuid4(),
            data=request,
        )

    repository_uow.repositories.create.assert_not_called()
    repository_uow.commit.assert_not_called()


def test_create_github_repository_duplicate_url(
    repository_service,
    repository_uow,
):
    project = Project(
        workspace_id=uuid4(),
        name="Project",
    )
    project.id=uuid4()
    print("hello",project,type(project),project.workspace_id)



    repository_uow.projects.get_by_id_and_user.return_value = project
    repository_uow.repositories.exists_by_url.return_value = True

    request = GithubRepositoryCreate(
        project_id=project.id,
        url="https://github.com/openai/test-repository.git",
    )

    with pytest.raises(RepositoryAlreadyExists):
        repository_service.create_github_repository(
            user_id=uuid4(),
            data=request,
        )

    repository_uow.repositories.create.assert_not_called()
    repository_uow.commit.assert_not_called()


def test_create_github_repository_extracts_name(
    repository_service,
    repository_uow,
):
    project = Project(
        workspace_id=uuid4(),
        name="Project",
    )
    project.id = uuid4()
    repository_uow.projects.get_by_id_and_user.return_value = project
    repository_uow.repositories.exists_by_url.return_value = False

    repository = Repository(
        project_id=project.id,
        name="my-project",
        provider=RepositoryProvider.GITHUB,
        url="https://github.com/user/my-project.git",
        default_branch="main",
        current_branch="main",
        status=RepositoryStatus.PENDING,
    )


    repository_uow.repositories.create.return_value = repository

    request = GithubRepositoryCreate(
        project_id=project.id,
        url="https://github.com/user/my-project.git",
    )

    repository_service.create_github_repository(
        user_id=uuid4(),
        data=request,
    )

    created_repository = repository_uow.repositories.create.call_args.args[0]

    assert created_repository.name == "my-project"
    assert created_repository.provider == RepositoryProvider.GITHUB
    assert created_repository.status == RepositoryStatus.PENDING


def test_create_uploaded_repository_success(
    repository_service,
    repository_uow,
):
    project = Project(
        workspace_id=uuid4(),
        name="Project",
    )
    project.id = uuid4()

    repository_uow.projects.get_by_id_and_user.return_value = project
    repository_uow.repositories.exists_by_name.return_value = False

    repository = Repository(
        project_id=project.id,
        name="uploaded-project",
        provider=RepositoryProvider.UPLOAD,
        url=None,
        default_branch="main",
        current_branch="main",
        status=RepositoryStatus.PENDING,
    )

    repository_uow.repositories.create.return_value = repository

    request = UploadRepositoryCreate(
        project_id=project.id,
        name="uploaded-project",
    )

    result = repository_service.create_uploaded_repository(
        user_id=uuid4(),
        data=request,
    )

    repository_uow.repositories.exists_by_name.assert_called_once_with(
        project_id=project.id,
        name="uploaded-project",
    )

    repository_uow.commit.assert_called_once()
    repository_uow.refresh.assert_called_once_with(repository)

    assert result is repository


def test_create_uploaded_repository_duplicate_name(
    repository_service,
    repository_uow,
):
    project = Project(
        workspace_id=uuid4(),
        name="Project",
    )
    project.id = uuid4()

    repository_uow.projects.get_by_id_and_user.return_value = project
    repository_uow.repositories.exists_by_name.return_value = True

    request = UploadRepositoryCreate(
        project_id=project.id,
        name="existing-repository",
    )

    with pytest.raises(RepositoryAlreadyExists):
        repository_service.create_uploaded_repository(
            user_id=uuid4(),
            data=request,
        )

    repository_uow.repositories.create.assert_not_called()
    repository_uow.commit.assert_not_called()


def test_get_repository_success(
    repository_service,
    repository_uow,
):
    repository = Repository(
        project_id=uuid4(),
        name="Repository",
        provider=RepositoryProvider.GITHUB,
        url="https://github.com/test/repository.git",
        default_branch="main",
        current_branch="main",
        status=RepositoryStatus.PENDING,
    )

    repository_uow.repositories.get_by_id_and_user.return_value = repository

    result = repository_service.get_repository(
        repository_id=repository.id,
        user_id=uuid4(),
    )

    assert result is repository


def test_get_repository_not_found(
    repository_service,
    repository_uow,
):
    repository_uow.repositories.get_by_id_and_user.return_value = None

    with pytest.raises(RepositoryNotFound):
        repository_service.get_repository(
            repository_id=uuid4(),
            user_id=uuid4(),
        )


def test_list_project_repositories_success(
    repository_service,
    repository_uow,
):
    project = Project(
        workspace_id=uuid4(),
        name="Project",
    )

    repositories = [
        Repository(
            project_id=project.id,
            name="repo-one",
            provider=RepositoryProvider.GITHUB,
            url="https://github.com/test/repo-one.git",
            default_branch="main",
            current_branch="main",
            status=RepositoryStatus.PENDING,
        ),
        Repository(
            project_id=project.id,
            name="repo-two",
            provider=RepositoryProvider.GITHUB,
            url="https://github.com/test/repo-two.git",
            default_branch="main",
            current_branch="main",
            status=RepositoryStatus.PENDING,
        ),
    ]

    repository_uow.projects.get_by_id_and_user.return_value = project
    repository_uow.repositories.list_by_project.return_value = repositories

    result = repository_service.list_project_repositories(
        project_id=project.id,
        user_id=uuid4(),
    )

    repository_uow.repositories.list_by_project.assert_called_once_with(
        project_id=project.id,
    )

    assert result == repositories


def test_list_project_repositories_project_not_found(
    repository_service,
    repository_uow,
):
    repository_uow.projects.get_by_id_and_user.return_value = None

    with pytest.raises(ProjectNotFound):
        repository_service.list_project_repositories(
            project_id=uuid4(),
            user_id=uuid4(),
        )

    repository_uow.repositories.list_by_project.assert_not_called()


def test_delete_repository(
    repository_service,
    repository_uow,
):
    repository = Repository(
        project_id=uuid4(),
        name="Repository",
        provider=RepositoryProvider.GITHUB,
        url="https://github.com/test/repository.git",
        default_branch="main",
        current_branch="main",
        status=RepositoryStatus.PENDING,
    )

    repository_uow.repositories.get_by_id_and_user.return_value = repository

    repository_service.delete_repository(
        repository_id=repository.id,
        user_id=uuid4(),
    )

    repository_uow.repositories.delete.assert_called_once_with(
        repository,
    )

    repository_uow.commit.assert_called_once()
