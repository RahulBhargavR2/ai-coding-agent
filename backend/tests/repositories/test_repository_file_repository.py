from uuid import uuid4

from app.models.enums import RepositoryProvider, RepositoryStatus
from app.models.project import Project
from app.models.repository import Repository
from app.models.repository_file import RepositoryFile
from app.models.workspace import Workspace

from app.repositories.repository_file_repository import RepositoryFileRepository

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


def create_repository(db_session, project):
    repository = Repository(
        project_id=project.id,
        name=f"Repository-{uuid4()}",
        provider=RepositoryProvider.GITHUB,
        url=f"https://github.com/test/{uuid4()}.git",
        default_branch="main",
        current_branch="main",
        status=RepositoryStatus.PENDING,
    )

    db_session.add(repository)
    db_session.flush()

    return repository


def create_file(
    db_session,
    repository,
    *,
    relative_path="app/main.py",
    file_name="main.py",
    extension=".py",
    language="python",
    size_bytes=100,
    sha256_hash=None,
    is_indexed=False,
    is_ignored=False,
):
    repository_file = RepositoryFile(
        repository_id=repository.id,
        relative_path=relative_path,
        file_name=file_name,
        extension=extension,
        language=language,
        size_bytes=size_bytes,
        sha256_hash=sha256_hash or uuid4().hex + uuid4().hex,
        is_indexed=is_indexed,
        is_ignored=is_ignored,
    )

    db_session.add(repository_file)
    db_session.flush()

    return repository_file


# ============================================================================
# Create
# ============================================================================


def test_create_repository_file(db_session, user):
    repository = RepositoryFileRepository(db_session)

    project = create_project(db_session, user)
    repo = create_repository(db_session, project)

    repository_file = RepositoryFile(
        repository_id=repo.id,
        relative_path="app/main.py",
        file_name="main.py",
        extension=".py",
        language="python",
        size_bytes=250,
        sha256_hash=uuid4().hex + uuid4().hex,
        is_indexed=False,
        is_ignored=False,
    )

    result = repository.create(repository_file)

    db_session.flush()

    assert result.id is not None
    assert result.repository_id == repo.id
    assert result.relative_path == "app/main.py"
    assert result.file_name == "main.py"
    assert result.language == "python"
    assert result.is_indexed is False
    assert result.is_ignored is False


# ============================================================================
# Get by ID
# ============================================================================


def test_get_by_id_returns_file(db_session, user):
    repository = RepositoryFileRepository(db_session)

    project = create_project(db_session, user)
    repo = create_repository(db_session, project)

    repository_file = create_file(
        db_session,
        repo,
        relative_path="app/service.py",
        file_name="service.py",
    )

    result = repository.get_by_id(repository_file.id)

    assert result is not None
    assert result.id == repository_file.id
    assert result.relative_path == "app/service.py"


def test_get_by_id_returns_none_for_unknown_file(db_session):
    repository = RepositoryFileRepository(db_session)

    result = repository.get_by_id(uuid4())

    assert result is None


# ============================================================================
# Ownership
# ============================================================================


def test_get_by_id_and_user_returns_file(
    db_session,
    user,
):
    repository = RepositoryFileRepository(db_session)

    project = create_project(db_session, user)
    repo = create_repository(db_session, project)

    repository_file = create_file(
        db_session,
        repo,
    )

    result = repository.get_by_id_and_user(
        file_id=repository_file.id,
        user_id=user.id,
    )

    assert result is not None
    assert result.id == repository_file.id


def test_get_by_id_and_user_returns_none_for_wrong_user(
    db_session,
    user,
    user_factory,
):
    repository = RepositoryFileRepository(db_session)

    project = create_project(db_session, user)
    repo = create_repository(db_session, project)

    repository_file = create_file(
        db_session,
        repo,
    )

    another_user = user_factory()

    result = repository.get_by_id_and_user(
        file_id=repository_file.id,
        user_id=another_user.id,
    )

    assert result is None


def test_get_by_id_and_user_returns_none_for_unknown_file(
    db_session,
    user,
):
    repository = RepositoryFileRepository(db_session)

    result = repository.get_by_id_and_user(
        file_id=uuid4(),
        user_id=user.id,
    )

    assert result is None


# ============================================================================
# List by Repository
# ============================================================================


def test_list_by_repository(db_session, user):
    repository = RepositoryFileRepository(db_session)

    project = create_project(db_session, user)
    repo = create_repository(db_session, project)

    file_one = create_file(
        db_session,
        repo,
        relative_path="app/main.py",
    )

    file_two = create_file(
        db_session,
        repo,
        relative_path="app/service.py",
        file_name="service.py",
    )

    result = repository.list_by_repository(repo.id)

    assert len(result) == 2
    assert {file.id for file in result} == {
        file_one.id,
        file_two.id,
    }


def test_list_by_repository_orders_by_relative_path(
    db_session,
    user,
):
    repository = RepositoryFileRepository(db_session)

    project = create_project(db_session, user)
    repo = create_repository(db_session, project)

    create_file(
        db_session,
        repo,
        relative_path="z.py",
        file_name="z.py",
    )

    create_file(
        db_session,
        repo,
        relative_path="a.py",
        file_name="a.py",
    )

    create_file(
        db_session,
        repo,
        relative_path="m.py",
        file_name="m.py",
    )

    result = repository.list_by_repository(repo.id)

    assert [file.relative_path for file in result] == [
        "a.py",
        "m.py",
        "z.py",
    ]


def test_list_by_repository_returns_empty_for_unknown_repository(
    db_session,
):
    repository = RepositoryFileRepository(db_session)

    result = repository.list_by_repository(uuid4())

    assert result == []


# ============================================================================
# Path existence
# ============================================================================


def test_exists_by_path_returns_true(
    db_session,
    user,
):
    repository = RepositoryFileRepository(db_session)

    project = create_project(db_session, user)
    repo = create_repository(db_session, project)

    create_file(
        db_session,
        repo,
        relative_path="app/main.py",
    )

    assert repository.exists_by_path(
        repository_id=repo.id,
        relative_path="app/main.py",
    )


def test_exists_by_path_returns_false_for_unknown_path(
    db_session,
    user,
):
    repository = RepositoryFileRepository(db_session)

    project = create_project(db_session, user)
    repo = create_repository(db_session, project)

    create_file(
        db_session,
        repo,
        relative_path="app/main.py",
    )

    assert not repository.exists_by_path(
        repository_id=repo.id,
        relative_path="app/service.py",
    )


def test_exists_by_path_is_repository_specific(
    db_session,
    user,
):
    repository = RepositoryFileRepository(db_session)

    project = create_project(db_session, user)

    repo_one = create_repository(db_session, project)
    repo_two = create_repository(db_session, project)

    create_file(
        db_session,
        repo_one,
        relative_path="app/main.py",
    )

    assert repository.exists_by_path(
        repository_id=repo_one.id,
        relative_path="app/main.py",
    )

    assert not repository.exists_by_path(
        repository_id=repo_two.id,
        relative_path="app/main.py",
    )


# ============================================================================
# Indexed status
# ============================================================================


def test_list_by_indexed_status_returns_indexed_files(
    db_session,
    user,
):
    repository = RepositoryFileRepository(db_session)

    project = create_project(db_session, user)
    repo = create_repository(db_session, project)

    indexed_file = create_file(
        db_session,
        repo,
        relative_path="indexed.py",
        file_name="indexed.py",
        is_indexed=True,
    )

    create_file(
        db_session,
        repo,
        relative_path="pending.py",
        file_name="pending.py",
        is_indexed=False,
    )

    result = repository.list_by_indexed_status(
        repository_id=repo.id,
        is_indexed=True,
    )

    assert len(result) == 1
    assert result[0].id == indexed_file.id
    assert result[0].is_indexed is True


def test_list_by_indexed_status_returns_unindexed_files(
    db_session,
    user,
):
    repository = RepositoryFileRepository(db_session)

    project = create_project(db_session, user)
    repo = create_repository(db_session, project)

    create_file(
        db_session,
        repo,
        relative_path="indexed.py",
        file_name="indexed.py",
        is_indexed=True,
    )

    pending_file = create_file(
        db_session,
        repo,
        relative_path="pending.py",
        file_name="pending.py",
        is_indexed=False,
    )

    result = repository.list_by_indexed_status(
        repository_id=repo.id,
        is_indexed=False,
    )

    assert len(result) == 1
    assert result[0].id == pending_file.id
    assert result[0].is_indexed is False


# ============================================================================
# Pending indexing
# ============================================================================


def test_list_pending_indexing(
    db_session,
    user,
):
    repository = RepositoryFileRepository(db_session)

    project = create_project(db_session, user)
    repo = create_repository(db_session, project)

    pending_one = create_file(
        db_session,
        repo,
        relative_path="app/main.py",
    )

    pending_two = create_file(
        db_session,
        repo,
        relative_path="app/service.py",
        file_name="service.py",
    )

    create_file(
        db_session,
        repo,
        relative_path="app/indexed.py",
        file_name="indexed.py",
        is_indexed=True,
    )

    result = repository.list_pending_indexing(repo.id)

    assert len(result) == 2
    assert {file.id for file in result} == {
        pending_one.id,
        pending_two.id,
    }

    assert all(file.is_indexed is False for file in result)


# ============================================================================
# Delete
# ============================================================================


def test_delete_repository_file(
    db_session,
    user,
):
    repository = RepositoryFileRepository(db_session)

    project = create_project(db_session, user)
    repo = create_repository(db_session, project)

    repository_file = create_file(
        db_session,
        repo,
    )

    repository.delete(repository_file)

    db_session.flush()

    result = repository.get_by_id(repository_file.id)

    assert result is None
