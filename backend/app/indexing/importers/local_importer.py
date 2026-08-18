from __future__ import annotations

import shutil
from pathlib import Path

from app.core.exceptions import BusinessValidationError
from app.models.enums import RepositoryProvider, RepositoryStatus
from app.models.repository import Repository


class LocalImporter:
    """
    Imports a local source-code repository into the agent's
    managed repository storage.

    Responsibilities:
    - Validate the source directory.
    - Copy the repository into managed storage.
    - Store the managed local path.
    - Update repository import status.

    This class does not:
    - Scan repository files.
    - Create RepositoryFile records.
    - Parse source code.
    - Create chunks.
    - Generate embeddings.
    - Update vector stores.
    """

    def __init__(
        self,
        storage_root: Path,
    ) -> None:
        self.storage_root = storage_root

    def import_repository(
        self,
        repository: Repository,
        source_path: Path,
    ) -> Repository:
        """
        Import a local repository into managed storage.

        Args:
            repository: Repository database entity.
            source_path: Existing local repository directory.

        Returns:
            Updated Repository instance.

        Raises:
            BusinessValidationError:
                If the repository or source directory is invalid.
        """

        self._validate_repository(repository)
        self._validate_source(source_path)

        destination = self._build_destination(repository)

        repository.status = RepositoryStatus.CLONING

        try:
            self._copy_repository(
                source_path=source_path,
                destination=destination,
            )

            repository.local_path = str(destination)
            repository.current_branch = self._get_current_branch(destination)
            repository.commit_hash = self._get_commit_hash(destination)
            repository.status = RepositoryStatus.INDEXING

            return repository

        except (OSError, shutil.Error, BusinessValidationError):
            repository.status = RepositoryStatus.FAILED

            self._cleanup_failed_import(destination)

            raise

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_repository(
        repository: Repository,
    ) -> None:
        """
        Validate that this importer can handle the repository.
        """

        if repository.provider != RepositoryProvider.LOCAL:
            raise BusinessValidationError(
                "LocalImporter can only import local repositories."
            )

    @staticmethod
    def _validate_source(
        source_path: Path,
    ) -> None:
        """
        Validate the supplied local repository directory.
        """

        if not source_path.exists():
            raise BusinessValidationError(
                f"Local repository does not exist: {source_path}"
            )

        if not source_path.is_dir():
            raise BusinessValidationError(
                f"Local repository path is not a directory: {source_path}"
            )

    # ------------------------------------------------------------------
    # Destination
    # ------------------------------------------------------------------

    def _build_destination(
        self,
        repository: Repository,
    ) -> Path:
        """
        Build an isolated managed-storage directory.

        Repository UUIDs prevent collisions between repositories
        with identical names.
        """

        destination = self.storage_root / str(repository.id)

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if destination.exists():
            raise BusinessValidationError(
                f"Repository destination already exists: {destination}"
            )

        return destination

    # ------------------------------------------------------------------
    # Copy
    # ------------------------------------------------------------------

    @staticmethod
    def _copy_repository(
        source_path: Path,
        destination: Path,
    ) -> None:
        """
        Copy the source repository into managed storage.

        Existing Git metadata is intentionally preserved because
        later Git-aware operations may need repository history.
        """

        shutil.copytree(
            source_path,
            destination,
        )

    # ------------------------------------------------------------------
    # Git metadata
    # ------------------------------------------------------------------

    @staticmethod
    def _get_current_branch(
        repository_path: Path,
    ) -> str:
        """
        Retrieve the currently checked-out Git branch.

        Local repositories may not be Git repositories, so an empty
        result is treated as an unavailable branch.
        """

        import subprocess

        try:
            result = subprocess.run(
                [
                    "git",
                    "-C",
                    str(repository_path),
                    "branch",
                    "--show-current",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        except (subprocess.CalledProcessError, OSError):
            return ""

        return result.stdout.strip()

    @staticmethod
    def _get_commit_hash(
        repository_path: Path,
    ) -> str | None:
        """
        Retrieve the current Git commit SHA.

        Returns None when the local directory is not a Git repository.
        """

        import subprocess

        try:
            result = subprocess.run(
                [
                    "git",
                    "-C",
                    str(repository_path),
                    "rev-parse",
                    "HEAD",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        except (subprocess.CalledProcessError, OSError):
            return None

        commit_hash = result.stdout.strip()

        return commit_hash or None

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    @staticmethod
    def _cleanup_failed_import(
        destination: Path,
    ) -> None:
        """
        Remove partially copied repository data after failure.
        """

        if destination.exists():
            shutil.rmtree(
                destination,
                ignore_errors=True,
            )
