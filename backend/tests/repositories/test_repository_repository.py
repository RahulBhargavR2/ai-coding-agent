from uuid import uuid4

from app.models.enums import RepositoryProvider, RepositoryStatus
from app.models.project import Project
from app.models.repository import Repository
from app.models.workspace import Workspace
from app.repositories.repository_repository import RepositoryRepository


def create_project(db_session, user):
    workspace = Workspace(
        user_id=user.id,
        name=f"Workspace-{uuid4()}",
    )

    db_session.add(workspace)
    db_session.flush()

    project = Project(
        workspace_id=workspace.id,
        name=f"Project-{uuid4()}",
    )

    db_session.add(project)
    db_session.flush()

    return project


def create_repository(
    db_session,
    project,
    *,
    name="test-repository",
    url="https://github.com/test/test-repository.git",
):
    repository = Repository(
        project_id=project.id,
        name=name,
        provider=RepositoryProvider.GITHUB,
        url=url,
        default_branch="main",
        current_branch="main",
        status=RepositoryStatus.PENDING,
    )

    db_session.add(repository)
    db_session.flush()

    return repository


def test_create_repository(db_session, user):
    repository = RepositoryRepository(db_session)

    project = create_project(db_session, user)

    repo = Repository(
        project_id=project.id,
        name="test-repository",
        provider=RepositoryProvider.GITHUB,
        url="https://github.com/test/test-repository.git",
        default_branch="main",
        current_branch="main",
        status=RepositoryStatus.PENDING,
    )

    result = repository.create(repo)

    db_session.flush()

    assert result.id is not None
    assert result.project_id == project.id
    assert result.name == "test-repository"


def test_get_by_id_and_user_returns_repository(
    db_session,
    user,
):
    repository = RepositoryRepository(db_session)

    project = create_project(db_session, user)
    repo = create_repository(db_session, project)

    result = repository.get_by_id_and_user(
        repository_id=repo.id,
        user_id=user.id,
    )

    assert result is not None
    assert result.id == repo.id


def test_get_by_id_and_user_returns_none_for_wrong_user(
    db_session,
    user,
    user_factory,
):
    repository = RepositoryRepository(db_session)

    project = create_project(db_session, user)
    repo = create_repository(db_session, project)

    another_user = user_factory()

    result = repository.get_by_id_and_user(
        repository_id=repo.id,
        user_id=another_user.id,
    )

    assert result is None


def test_get_by_id_and_user_returns_none_for_unknown_repository(
    db_session,
    user,
):
    repository = RepositoryRepository(db_session)

    result = repository.get_by_id_and_user(
        repository_id=uuid4(),
        user_id=user.id,
    )

    assert result is None


def test_list_by_project(db_session, user):
    repository = RepositoryRepository(db_session)

    project = create_project(db_session, user)

    repo_one = create_repository(
        db_session,
        project,
        name="repo-one",
        url="https://github.com/test/repo-one.git",
    )

    repo_two = create_repository(
        db_session,
        project,
        name="repo-two",
        url="https://github.com/test/repo-two.git",
    )

    result = repository.list_by_project(project.id)

    assert len(result) == 2
    assert {repo.id for repo in result} == {
        repo_one.id,
        repo_two.id,
    }


def test_list_by_project_returns_empty_for_unknown_project(
    db_session,
):
    repository = RepositoryRepository(db_session)

    result = repository.list_by_project(uuid4())

    assert result == []


def test_exists_by_name(
    db_session,
    user,
):
    repository = RepositoryRepository(db_session)

    project = create_project(db_session, user)

    create_repository(
        db_session,
        project,
        name="My Repository",
    )

    assert repository.exists_by_name(
        project_id=project.id,
        name="My Repository",
    )


def test_exists_by_name_is_case_insensitive(
    db_session,
    user,
):
    repository = RepositoryRepository(db_session)

    project = create_project(db_session, user)

    create_repository(
        db_session,
        project,
        name="My Repository",
    )

    assert repository.exists_by_name(
        project_id=project.id,
        name="my repository",
    )


def test_exists_by_name_returns_false_for_unknown_name(
    db_session,
    user,
):
    repository = RepositoryRepository(db_session)

    project = create_project(db_session, user)

    assert not repository.exists_by_name(
        project_id=project.id,
        name="Unknown Repository",
    )


def test_exists_by_url(
    db_session,
    user,
):
    repository = RepositoryRepository(db_session)

    project = create_project(db_session, user)

    url = "https://github.com/test/my-repository.git"

    create_repository(
        db_session,
        project,
        url=url,
    )

    assert repository.exists_by_url(
        project_id=project.id,
        url=url,
    )


def test_exists_by_url_returns_false_for_unknown_url(
    db_session,
    user,
):
    repository = RepositoryRepository(db_session)

    project = create_project(db_session, user)

    assert not repository.exists_by_url(
        project_id=project.id,
        url="https://github.com/test/unknown.git",
    )


def test_list_by_status(db_session, user):
    repository = RepositoryRepository(db_session)

    project = create_project(db_session, user)

    pending = create_repository(
        db_session,
        project,
        name="pending-repo",
        url="https://github.com/test/pending.git",
    )

    indexed = create_repository(
        db_session,
        project,
        name="indexed-repo",
        url="https://github.com/test/indexed.git",
    )

    indexed.status = RepositoryStatus.INDEXED

    db_session.flush()

    result = repository.list_by_status(
        RepositoryStatus.PENDING,
    )

    assert len(result) == 1
    assert result[0].id == pending.id
    assert result[0].id != indexed.id


def test_update_status(db_session, user):
    repository = RepositoryRepository(db_session)

    project = create_project(db_session, user)

    repo = create_repository(
        db_session,
        project,
    )

    result = repository.update_status(
        repository=repo,
        status=RepositoryStatus.INDEXED,
    )

    assert result is repo
    assert result.status == RepositoryStatus.INDEXED


def test_delete_repository(db_session, user):
    repository = RepositoryRepository(db_session)

    project = create_project(db_session, user)
    repo = create_repository(db_session, project)

    repository.delete(repo)

    db_session.flush()

    result = repository.get_by_id_and_user(
        repository_id=repo.id,
        user_id=user.id,
    )

    assert result is None
