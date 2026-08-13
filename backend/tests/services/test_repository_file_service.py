from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.core.exceptions import (
    BusinessValidationError,
    RepositoryNotFound,
    RepositoryFileNotFound,
    RepositoryFileAlreadyExists
)
from app.models.repository import Repository
from app.models.repository_file import RepositoryFile
from app.services.workspace.repository_file_service import RepositoryFileService


@pytest.fixture
def repository_file_uow():
    uow = Mock()

    uow.repositories = Mock()
    uow.repository_files = Mock()

    return uow


@pytest.fixture
def repository_file_service(repository_file_uow):
    return RepositoryFileService(repository_file_uow)


def create_repository_file(
    repository_id=None,
    *,
    relative_path="app/main.py",
):
    return RepositoryFile(
        repository_id=repository_id or uuid4(),
        relative_path=relative_path,
        file_name=relative_path.split("/")[-1],
        extension=".py",
        language="python",
        size_bytes=100,
        sha256_hash=uuid4().hex + uuid4().hex,
        is_indexed=False,
        is_ignored=False,
    )


# ============================================================================
# Create
# ============================================================================


def test_create_file(
    repository_file_service,
    repository_file_uow,
):
    user_id = uuid4()
    repository_id = uuid4()

    repository = Mock(spec=Repository)
    repository.id = repository_id

    repository_file = create_repository_file(
        repository_id=repository_id,
    )

    repository_file_uow.repositories.get_by_id_and_user.return_value = repository

    repository_file_uow.repository_files.exists_by_path.return_value = False

    repository_file_uow.repository_files.create.return_value = repository_file

    result = repository_file_service.create_file(
        user_id=user_id,
        repository_id=repository_id,
        repository_file=repository_file,
    )

    repository_file_uow.repositories.get_by_id_and_user.assert_called_once_with(
        repository_id=repository_id,
        user_id=user_id,
    )

    repository_file_uow.repository_files.exists_by_path.assert_called_once_with(
        repository_id=repository_id,
        relative_path="app/main.py",
    )

    repository_file_uow.repository_files.create.assert_called_once_with(
        repository_file,
    )

    repository_file_uow.commit.assert_called_once()
    repository_file_uow.refresh.assert_called_once_with(repository_file)

    assert result is repository_file
    assert repository_file.repository_id == repository_id


def test_create_file_repository_not_found(
    repository_file_service,
    repository_file_uow,
):
    repository_file_uow.repositories.get_by_id_and_user.return_value = None

    repository_file = create_repository_file()

    with pytest.raises(RepositoryNotFound):
        repository_file_service.create_file(
            user_id=uuid4(),
            repository_id=uuid4(),
            repository_file=repository_file,
        )

    repository_file_uow.repository_files.create.assert_not_called()
    repository_file_uow.commit.assert_not_called()


def test_create_file_duplicate_path(
    repository_file_service,
    repository_file_uow,
):
    repository_id = uuid4()

    repository = Mock(spec=Repository)
    repository.id = repository_id

    repository_file_uow.repositories.get_by_id_and_user.return_value = repository

    repository_file_uow.repository_files.exists_by_path.return_value = True

    repository_file = create_repository_file(
        repository_id=repository_id,
    )

    with pytest.raises(RepositoryFileAlreadyExists):
        repository_file_service.create_file(
            user_id=uuid4(),
            repository_id=repository_id,
            repository_file=repository_file,
        )

    repository_file_uow.repository_files.create.assert_not_called()
    repository_file_uow.commit.assert_not_called()


# ============================================================================
# Get
# ============================================================================


def test_get_file(
    repository_file_service,
    repository_file_uow,
):
    file_id = uuid4()
    user_id = uuid4()

    repository_file = create_repository_file()

    repository_file.id = file_id

    repository_file_uow.repository_files.get_by_id_and_user.return_value = (
        repository_file
    )

    result = repository_file_service.get_file(
        file_id=file_id,
        user_id=user_id,
    )

    repository_file_uow.repository_files.get_by_id_and_user.assert_called_once_with(
        file_id=file_id,
        user_id=user_id,
    )

    assert result is repository_file


def test_get_file_not_found(
    repository_file_service,
    repository_file_uow,
):
    repository_file_uow.repository_files.get_by_id_and_user.return_value = None

    with pytest.raises(RepositoryFileNotFound):
        repository_file_service.get_file(
            file_id=uuid4(),
            user_id=uuid4(),
        )


# ============================================================================
# List
# ============================================================================


def test_list_repository_files(
    repository_file_service,
    repository_file_uow,
):
    user_id = uuid4()
    repository_id = uuid4()

    repository = Mock(spec=Repository)
    repository.id = repository_id

    files = [
        create_repository_file(
            repository_id=repository_id,
            relative_path="app/main.py",
        ),
        create_repository_file(
            repository_id=repository_id,
            relative_path="app/service.py",
        ),
    ]

    repository_file_uow.repositories.get_by_id_and_user.return_value = repository

    repository_file_uow.repository_files.list_by_repository.return_value = files

    result = repository_file_service.list_repository_files(
        repository_id=repository_id,
        user_id=user_id,
    )

    repository_file_uow.repository_files.list_by_repository.assert_called_once_with(
        repository_id=repository_id,
    )

    assert result == files


def test_list_repository_files_repository_not_found(
    repository_file_service,
    repository_file_uow,
):
    repository_file_uow.repositories.get_by_id_and_user.return_value = None

    with pytest.raises(RepositoryNotFound):
        repository_file_service.list_repository_files(
            repository_id=uuid4(),
            user_id=uuid4(),
        )

    repository_file_uow.repository_files.list_by_repository.assert_not_called()


# ============================================================================
# Pending files
# ============================================================================


def test_list_pending_files(
    repository_file_service,
    repository_file_uow,
):
    user_id = uuid4()
    repository_id = uuid4()

    repository = Mock(spec=Repository)
    repository.id = repository_id

    files = [
        create_repository_file(
            repository_id=repository_id,
            relative_path="app/main.py",
        ),
    ]

    repository_file_uow.repositories.get_by_id_and_user.return_value = repository

    repository_file_uow.repository_files.list_pending_indexing.return_value = files

    result = repository_file_service.list_pending_files(
        repository_id=repository_id,
        user_id=user_id,
    )

    repository_file_uow.repository_files.list_pending_indexing.assert_called_once_with(
        repository_id=repository_id,
    )

    assert result == files


def test_list_pending_files_repository_not_found(
    repository_file_service,
    repository_file_uow,
):
    repository_file_uow.repositories.get_by_id_and_user.return_value = None

    with pytest.raises(RepositoryNotFound):
        repository_file_service.list_pending_files(
            repository_id=uuid4(),
            user_id=uuid4(),
        )

    repository_file_uow.repository_files.list_pending_indexing.assert_not_called()


# ============================================================================
# Mark indexed
# ============================================================================


def test_mark_indexed(
    repository_file_service,
    repository_file_uow,
):
    file_id = uuid4()
    user_id = uuid4()

    repository_file = create_repository_file()
    repository_file.id = file_id
    repository_file.is_indexed = False

    repository_file_uow.repository_files.get_by_id_and_user.return_value = (
        repository_file
    )

    result = repository_file_service.mark_indexed(
        file_id=file_id,
        user_id=user_id,
    )

    assert result is repository_file
    assert repository_file.is_indexed is True




def test_mark_indexed_file_not_found(
    repository_file_service,
    repository_file_uow,
):
    repository_file_uow.repository_files.get_by_id_and_user.return_value = None

    with pytest.raises(RepositoryFileNotFound):
        repository_file_service.mark_indexed(
            file_id=uuid4(),
            user_id=uuid4(),
        )

    repository_file_uow.commit_and_refresh.assert_not_called()


# ============================================================================
# Mark unindexed
# ============================================================================


def test_mark_unindexed(
    repository_file_service,
    repository_file_uow,
):
    file_id = uuid4()
    user_id = uuid4()

    repository_file = create_repository_file()
    repository_file.id = file_id
    repository_file.is_indexed = True

    repository_file_uow.repository_files.get_by_id_and_user.return_value = (
        repository_file
    )

    result = repository_file_service.mark_unindexed(
        file_id=file_id,
        user_id=user_id,
    )

    assert result is repository_file
    assert repository_file.is_indexed is False

    # repository_file_uow.commit_and_refresh.assert_called_once_with(
    #     repository_file,
    # )


# ============================================================================
# Delete
# ============================================================================


def test_delete_file(
    repository_file_service,
    repository_file_uow,
):
    file_id = uuid4()
    user_id = uuid4()

    repository_file = create_repository_file()
    repository_file.id = file_id

    repository_file_uow.repository_files.get_by_id_and_user.return_value = (
        repository_file
    )

    repository_file_service.delete_file(
        file_id=file_id,
        user_id=user_id,
    )

    repository_file_uow.repository_files.delete.assert_called_once_with(
        repository_file,
    )

    repository_file_uow.commit.assert_called_once()


def test_delete_file_not_found(
    repository_file_service,
    repository_file_uow,
):
    repository_file_uow.repository_files.get_by_id_and_user.return_value = None

    with pytest.raises(RepositoryFileNotFound):
        repository_file_service.delete_file(
            file_id=uuid4(),
            user_id=uuid4(),
        )

    repository_file_uow.repository_files.delete.assert_not_called()
    repository_file_uow.commit.assert_not_called()
