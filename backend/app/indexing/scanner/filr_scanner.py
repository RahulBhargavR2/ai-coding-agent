from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from app.core.exceptions import BusinessValidationError
from app.indexing.scanner.ignore_rules import IgnoreRules
from app.indexing.scanner.language_detector import LanguageDetector
from app.models.repository import Repository
from app.models.repository_file import RepositoryFile


class FileScanner:
    """
    Scans an imported repository and converts source files into
    RepositoryFile entities.

    Responsibilities:
    - Traverse the repository filesystem.
    - Apply ignore rules.
    - Detect file languages.
    - Calculate file metadata.
    - Calculate SHA-256 hashes.
    - Produce RepositoryFile entities.

    This class does not:
    - Persist files to the database.
    - Parse source code.
    - Create chunks.
    - Generate embeddings.
    - Update vector stores.
    """

    def __init__(
        self,
        ignore_rules: IgnoreRules | None = None,
        language_detector: LanguageDetector | None = None,
    ) -> None:
        self.ignore_rules = ignore_rules or IgnoreRules()
        self.language_detector = language_detector or LanguageDetector()

    def scan(
        self,
        repository: Repository,
    ) -> list[RepositoryFile]:
        """
        Scan all supported files in a repository.

        Args:
            repository: Imported repository entity.

        Returns:
            List of RepositoryFile entities.

        Raises:
            BusinessValidationError:
                If the repository has no valid local path.
        """

        repository_root = self._get_repository_root(repository)

        repository_files: list[RepositoryFile] = []

        for path in self._walk_repository(repository_root):
            if self.ignore_rules.should_ignore_file(path):
                continue

            repository_file = self._build_repository_file(
                repository=repository,
                repository_root=repository_root,
                file_path=path,
            )

            repository_files.append(repository_file)

        return repository_files

    # ------------------------------------------------------------------
    # Repository root
    # ------------------------------------------------------------------

    @staticmethod
    def _get_repository_root(
        repository: Repository,
    ) -> Path:
        """
        Resolve the local filesystem path of an imported repository.
        """

        if not repository.local_path:
            raise BusinessValidationError("Repository has not been imported yet.")

        repository_root = Path(repository.local_path)

        if not repository_root.exists():
            raise BusinessValidationError(
                f"Repository path does not exist: {repository_root}"
            )

        if not repository_root.is_dir():
            raise BusinessValidationError(
                f"Repository path is not a directory: {repository_root}"
            )

        return repository_root.resolve()

    # ------------------------------------------------------------------
    # Filesystem traversal
    # ------------------------------------------------------------------

    def _walk_repository(
        self,
        repository_root: Path,
    ):
        """
        Recursively walk the repository while pruning ignored directories.

        Ignored directories are removed from traversal instead of merely
        skipping their files afterward. This prevents unnecessary filesystem
        traversal into directories such as node_modules or .git.
        """

        for current_directory, directories, files in repository_root.walk(
            top_down=True,
        ):
            directories[:] = [
                directory
                for directory in directories
                if not self.ignore_rules.should_ignore_directory(
                    current_directory / directory
                )
            ]

            for filename in files:
                file_path = current_directory / filename

                if file_path.is_symlink():
                    continue

                if not file_path.is_file():
                    continue

                yield file_path

    # ------------------------------------------------------------------
    # RepositoryFile construction
    # ------------------------------------------------------------------

    def _build_repository_file(
        self,
        repository: Repository,
        repository_root: Path,
        file_path: Path,
    ) -> RepositoryFile:
        """
        Build a RepositoryFile entity from a filesystem file.
        """

        relative_path = file_path.relative_to(repository_root).as_posix()

        file_name = file_path.name

        extension = file_path.suffix.lower() or None

        language = self.language_detector.detect(file_path)

        size_bytes = file_path.stat().st_size

        sha256_hash = self._calculate_sha256(file_path)

        last_modified_at = self._get_last_modified_at(file_path)

        return RepositoryFile(
            repository_id=repository.id,
            relative_path=relative_path,
            file_name=file_name,
            extension=extension,
            language=language,
            size_bytes=size_bytes,
            sha256_hash=sha256_hash,
            last_modified_at=last_modified_at,
            is_indexed=False,
            is_ignored=False,
        )

    # ------------------------------------------------------------------
    # Hashing
    # ------------------------------------------------------------------

    @staticmethod
    def _calculate_sha256(
        file_path: Path,
    ) -> str:
        """
        Calculate the SHA-256 hash of a file.

        The file is processed in chunks so that large files do not
        need to be loaded entirely into memory.
        """

        digest = hashlib.sha256()

        with file_path.open("rb") as file:
            while chunk := file.read(1024 * 1024):
                digest.update(chunk)

        return digest.hexdigest()

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    @staticmethod
    def _get_last_modified_at(
        file_path: Path,
    ) -> datetime:
        """
        Return the file's last modification timestamp as a timezone-aware
        UTC datetime.
        """

        modified_timestamp = file_path.stat().st_mtime

        return datetime.fromtimestamp(
            modified_timestamp,
            tz=timezone.utc,
        )
