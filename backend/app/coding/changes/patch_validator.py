from pathlib import Path

from app.coding.changes.change import ChangeOperation, FileChange
from app.coding.changes.patch import Patch


class PatchValidationError(ValueError):
    """Raised when a patch cannot safely be applied."""


class PatchValidator:
    """
    Validates a Patch against a repository before it is applied.
    """

    def validate(
        self,
        patch: Patch,
        repository_path: Path,
    ) -> None:
        repository_path = repository_path.resolve()

        for change in patch.changes:
            self._validate_path(
                change.path,
                repository_path,
            )

            if change.operation == ChangeOperation.RENAME:
                if change.new_path is None:
                    raise PatchValidationError("Rename requires new_path")

                self._validate_path(
                    change.new_path,
                    repository_path,
                )

            self._validate_change(
                change,
                repository_path,
            )

    def _validate_path(
        self,
        path: str,
        repository_path: Path,
    ) -> Path:
        candidate = (repository_path / path).resolve()

        try:
            candidate.relative_to(repository_path)
        except ValueError as exc:
            raise PatchValidationError(f"Path escapes repository: {path}") from exc

        return candidate

    def _validate_change(
        self,
        change: FileChange,
        repository_path: Path,
    ) -> None:
        file_path = self._validate_path(
            change.path,
            repository_path,
        )

        if change.operation == ChangeOperation.CREATE:
            if file_path.exists():
                raise PatchValidationError(f"File already exists: {change.path}")

        elif change.operation in (
            ChangeOperation.MODIFY,
            ChangeOperation.DELETE,
        ):
            if not file_path.exists():
                raise PatchValidationError(f"File does not exist: {change.path}")

            if not file_path.is_file():
                raise PatchValidationError(f"Path is not a file: {change.path}")

            current_content = file_path.read_text()

            if current_content != change.original_content:
                raise PatchValidationError(
                    f"File changed since retrieval: {change.path}"
                )

        elif change.operation == ChangeOperation.RENAME:
            if not file_path.exists():
                raise PatchValidationError(f"File does not exist: {change.path}")

            if not file_path.is_file():
                raise PatchValidationError(f"Path is not a file: {change.path}")

            current_content = file_path.read_text()

            if current_content != change.original_content:
                raise PatchValidationError(
                    f"File changed since retrieval: {change.path}"
                )

            destination = self._validate_path(
                change.new_path or "",
                repository_path,
            )

            if destination.exists():
                raise PatchValidationError(
                    f"Destination already exists: {change.new_path}"
                )
