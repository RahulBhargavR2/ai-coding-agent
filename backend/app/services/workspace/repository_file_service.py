from __future__ import annotations

from uuid import UUID

from app.core.exceptions import (
    RepositoryFileAlreadyExists,
    RepositoryFileNotFound,
    RepositoryNotFound,
)
from app.models.repository_file import RepositoryFile
from app.dependencies.uow import UnitOfWorkDep


class RepositoryFileService:
    """
    Handles repository-file metadata and indexing state.

    Filesystem discovery, parsing, chunking, and embedding generation
    are handled by dedicated indexing components.
    """

    def __init__(
        self,
        uow: UnitOfWork,
    ) -> None:
        self.uow = uow

    def get_file(
        self,
        file_id: UUID,
        user_id: UUID,
    ) -> RepositoryFile:

        repository_file = self.uow.repository_files.get_by_id_and_user(
            file_id=file_id,
            user_id=user_id,
        )

        if repository_file is None:
            raise RepositoryFileNotFound(f"Repository file {file_id} not found.")

        return repository_file

    def list_repository_files(
        self,
        repository_id: UUID,
        user_id: UUID,
    ) -> list[RepositoryFile]:

        repository = self.uow.repositories.get_by_id_and_user(
            repository_id=repository_id,
            user_id=user_id,
        )

        if repository is None:
            raise RepositoryNotFound(f"Repository {repository_id} not found.")

        return self.uow.repository_files.list_by_repository(
            repository_id=repository_id,
        )

    def list_pending_files(
        self,
        repository_id: UUID,
        user_id: UUID,
    ) -> list[RepositoryFile]:

        repository = self.uow.repositories.get_by_id_and_user(
            repository_id=repository_id,
            user_id=user_id,
        )

        if repository is None:
            raise RepositoryNotFound(f"Repository {repository_id} not found.")

        return self.uow.repository_files.list_pending_indexing(
            repository_id=repository_id,
        )

    def create_file(
        self,
        user_id: UUID,
        repository_id: UUID,
        repository_file: RepositoryFile,
    ) -> RepositoryFile:

        repository = self.uow.repositories.get_by_id_and_user(
            repository_id=repository_id,
            user_id=user_id,
        )

        if repository is None:
            raise RepositoryNotFound(f"Repository {repository_id} not found.")

        if repository_file.repository_id != repository_id:
            raise BusinessValidationError(
                "Repository file does not belong to " "the specified repository."
            )

        if self.uow.repository_files.exists_by_path(
            repository_id=repository_id,
            relative_path=repository_file.relative_path,
        ):
            raise RepositoryFileAlreadyExists(
                f"File '{repository_file.relative_path}' "
                f"already exists in the repository."
            )

        repository_file = self.uow.repository_files.create(
            repository_file,
        )

        self.uow.commit()
        self.uow.refresh(repository_file)

        return repository_file

    def mark_indexed(
        self,
        file_id: UUID,
        user_id: UUID,
    ) -> RepositoryFile:

        repository_file = self.get_file(
            file_id=file_id,
            user_id=user_id,
        )

        repository_file.is_indexed = True

        self.uow.commit()
        self.uow.refresh(repository_file)

        return repository_file

    def mark_unindexed(
        self,
        file_id: UUID,
        user_id: UUID,
    ) -> RepositoryFile:

        repository_file = self.get_file(
            file_id=file_id,
            user_id=user_id,
        )

        repository_file.is_indexed = False

        self.uow.commit()
        self.uow.refresh(repository_file)

        return repository_file

    def delete_file(
        self,
        file_id: UUID,
        user_id: UUID,
    ) -> None:

        repository_file = self.get_file(
            file_id=file_id,
            user_id=user_id,
        )

        self.uow.repository_files.delete(repository_file)
        self.uow.commit()
