from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

from app.core.exceptions import BusinessValidationError
from app.models.enums import RepositoryProvider, RepositoryStatus
from app.models.repository import Repository


class ZipImporter:
    """
    Imports a repository from a ZIP archive.

    Responsibilities:
    - Validate the ZIP archive.
    - Safely extract the archive.
    - Prevent path traversal attacks.
    - Normalize the extracted repository directory.
    - Store the local repository path.
    - Update repository import status.

    This class does not:
    - Create the Repository database record.
    - Scan repository files.
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
        archive_path: Path,
    ) -> Repository:
        """
        Import a repository from a ZIP archive.

        The Repository instance must already exist in the database.

        Args:
            repository: Repository database entity.
            archive_path: Path to the uploaded ZIP archive.

        Returns:
            Updated Repository instance.

        Raises:
            BusinessValidationError:
                If validation or extraction fails.
        """

        self._validate_repository(repository)
        self._validate_archive(archive_path)

        destination = self._build_destination(repository)

        repository.status = RepositoryStatus.CLONING

        try:
            self._extract_archive(
                archive_path=archive_path,
                destination=destination,
            )

            repository_root = self._resolve_repository_root(destination)

            repository.local_path = str(repository_root)
            repository.status = RepositoryStatus.INDEXING

            return repository

        except (OSError, zipfile.BadZipFile, BusinessValidationError):
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
        Validate that the repository can be handled by this importer.
        """

        if repository.provider != RepositoryProvider.UPLOAD:
            raise BusinessValidationError(
                "ZipImporter can only import uploaded repositories."
            )

    @staticmethod
    def _validate_archive(
        archive_path: Path,
    ) -> None:
        """
        Validate that the supplied file exists and is a ZIP archive.
        """

        if not archive_path.exists():
            raise BusinessValidationError(f"ZIP archive does not exist: {archive_path}")

        if not archive_path.is_file():
            raise BusinessValidationError(
                f"ZIP archive path is not a file: {archive_path}"
            )

        if not zipfile.is_zipfile(archive_path):
            raise BusinessValidationError(
                "The uploaded file is not a valid ZIP archive."
            )

    # ------------------------------------------------------------------
    # Destination
    # ------------------------------------------------------------------

    def _build_destination(
        self,
        repository: Repository,
    ) -> Path:
        """
        Build an isolated extraction directory.

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
    # Extraction
    # ------------------------------------------------------------------

    def _extract_archive(
        self,
        archive_path: Path,
        destination: Path,
    ) -> None:
        """
        Safely extract a ZIP archive.

        Every archive member is validated before extraction to prevent
        paths such as ../../etc/passwd from escaping the destination.
        """

        destination = destination.resolve()

        try:
            with zipfile.ZipFile(archive_path, "r") as archive:
                for member in archive.infolist():
                    member_path = (destination / member.filename).resolve()

                    if not self._is_safe_path(
                        destination=destination,
                        member_path=member_path,
                    ):
                        raise BusinessValidationError(
                            "ZIP archive contains an unsafe file path."
                        )

                destination.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                archive.extractall(destination)

        except zipfile.BadZipFile as exc:
            raise BusinessValidationError(
                "The uploaded ZIP archive is corrupted or invalid."
            ) from exc

    # ------------------------------------------------------------------
    # Repository root
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_repository_root(
        destination: Path,
    ) -> Path:
        """
        Resolve the actual repository root.

        GitHub-generated ZIP files commonly contain one top-level
        directory such as:

            repository-main/
                app/
                README.md

        In that case, the top-level directory is treated as the
        repository root.

        If the archive contains multiple top-level entries, the
        extraction directory itself is used.
        """

        entries = list(destination.iterdir())

        if len(entries) == 1 and entries[0].is_dir():
            return entries[0]

        return destination

    # ------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------

    @staticmethod
    def _is_safe_path(
        destination: Path,
        member_path: Path,
    ) -> bool:
        """
        Check whether an extracted ZIP member remains inside
        the intended destination directory.
        """

        try:
            member_path.relative_to(destination)
        except ValueError:
            return False

        return True

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    @staticmethod
    def _cleanup_failed_import(
        destination: Path,
    ) -> None:
        """
        Remove partially extracted repository data after failure.
        """

        if destination.exists():
            shutil.rmtree(
                destination,
                ignore_errors=True,
            )
