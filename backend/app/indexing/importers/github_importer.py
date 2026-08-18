from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
from pathlib import Path

from app.core.exceptions import BusinessValidationError
from app.models.enums import RepositoryStatus
from app.models.repository import Repository


class GitHubImporter:
    """
    Imports a public GitHub repository into the local repository storage.

    Responsibilities:
    - Validate the GitHub repository URL.
    - Clone the repository.
    - Checkout the requested branch.
    - Capture the current commit SHA.
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

    GITHUB_URL_PATTERN = re.compile(
        r"^https://github\.com/"
        r"(?P<owner>[A-Za-z0-9_.-]+)/"
        r"(?P<repository>[A-Za-z0-9_.-]+)"
        r"(?:\.git)?/?$"
    )

    def __init__(
        self,
        storage_root: Path,
    ) -> None:
        self.storage_root = storage_root

    def import_repository(
        self,
        repository: Repository,
    ) -> Repository:
        """
        Clone a public GitHub repository.

        The Repository instance must already exist in the database.

        Returns:
            Updated Repository instance.

        Raises:
            BusinessValidationError:
                If the repository is invalid or cloning fails.
        """

        self._validate_repository(repository)

        destination = self._build_destination(repository)

        repository.status = RepositoryStatus.CLONING

        try:
            self._clone_repository(
                url=repository.url,
                destination=destination,
                branch=repository.current_branch,
            )

            repository.local_path = str(destination)
            repository.commit_hash = self._get_commit_hash(destination)
            repository.current_branch = self._get_current_branch(destination)
            repository.status = RepositoryStatus.INDEXING

            return repository

        except (subprocess.SubprocessError, OSError, BusinessValidationError):
            repository.status = RepositoryStatus.FAILED

            self._cleanup_failed_import(destination)

            raise

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_repository(
        self,
        repository: Repository,
    ) -> None:
        """
        Validate that the repository can be imported by this importer.
        """

        if repository.provider.value != "github":
            raise BusinessValidationError(
                "GitHubImporter can only import GitHub repositories."
            )

        if not repository.url:
            raise BusinessValidationError("GitHub repository URL is required.")

        if self.GITHUB_URL_PATTERN.fullmatch(repository.url) is None:
            raise BusinessValidationError("Invalid public GitHub repository URL.")

        if not repository.current_branch:
            raise BusinessValidationError("Repository branch is required.")

    # ------------------------------------------------------------------
    # Destination
    # ------------------------------------------------------------------

    def _build_destination(
        self,
        repository: Repository,
    ) -> Path:
        """
        Build an isolated local directory for the repository.

        UUID is used instead of the repository name to prevent collisions
        between repositories with the same name across different projects.
        """

        destination = self.storage_root / str(repository.id)

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        return destination

    # ------------------------------------------------------------------
    # Git operations
    # ------------------------------------------------------------------

    @staticmethod
    def _clone_repository(
        url: str,
        destination: Path,
        branch: str,
    ) -> None:
        """
        Clone the requested branch from a public GitHub repository.
        """

        if destination.exists():
            raise BusinessValidationError(
                f"Repository destination already exists: {destination}"
            )

        command = [
            "git",
            "clone",
            "--branch",
            branch,
            "--single-branch",
            url,
            str(destination),
        ]

        try:
            subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=300,
            )
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.strip()

            raise BusinessValidationError(
                f"Failed to clone GitHub repository: {stderr}"
            ) from exc

        except subprocess.TimeoutExpired as exc:
            raise BusinessValidationError(
                "GitHub repository cloning timed out."
            ) from exc

    # ------------------------------------------------------------------
    # Repository metadata
    # ------------------------------------------------------------------

    @staticmethod
    def _get_commit_hash(
        repository_path: Path,
    ) -> str:
        """
        Retrieve the SHA of the currently checked-out commit.
        """

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

        commit_hash = result.stdout.strip()

        if not commit_hash:
            raise BusinessValidationError("Unable to determine repository commit hash.")

        return commit_hash

    @staticmethod
    def _get_current_branch(
        repository_path: Path,
    ) -> str:
        """
        Retrieve the currently checked-out branch.
        """

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

        branch = result.stdout.strip()

        if not branch:
            raise BusinessValidationError("Unable to determine repository branch.")

        return branch

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    @staticmethod
    def _cleanup_failed_import(
        destination: Path,
    ) -> None:
        """
        Remove partially cloned repository data after a failed import.
        """

        if destination.exists():
            shutil.rmtree(
                destination,
                ignore_errors=True,
            )
