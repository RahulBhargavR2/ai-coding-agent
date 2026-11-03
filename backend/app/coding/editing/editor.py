from pathlib import Path

from app.coding.changes.change import ChangeOperation, FileChange
from app.coding.changes.patch import Patch
from app.coding.changes.patch_validator import PatchValidator


class EditResult:
    """
    Result of applying a patch to a repository.
    """

    def __init__(
        self,
        *,
        success: bool,
        files_changed: list[str],
        error: str | None = None,
    ) -> None:
        self.success = success
        self.files_changed = files_changed
        self.error = error


class CodeEditor:
    """
    Applies validated code changes to a repository.
    """

    def __init__(
        self,
        validator: PatchValidator | None = None,
    ) -> None:
        self.validator = validator or PatchValidator()

    async def apply(
        self,
        patch: Patch,
        repository_path: Path,
    ) -> EditResult:
        """
        Validate and apply a patch.

        No changes are made if validation fails.
        """

        try:
            repository_path = repository_path.resolve()

            self.validator.validate(
                patch,
                repository_path,
            )

            backups = self._create_backups(
                patch,
                repository_path,
            )

            try:
                files_changed = self._apply_changes(
                    patch,
                    repository_path,
                )

            except Exception:
                self._restore_backups(
                    backups,
                    repository_path,
                )
                raise

            return EditResult(
                success=True,
                files_changed=files_changed,
            )

        except Exception as exc:
            return EditResult(
                success=False,
                files_changed=[],
                error=str(exc),
            )

    def _create_backups(
        self,
        patch: Patch,
        repository_path: Path,
    ) -> dict[str, str]:
        backups: dict[str, str] = {}

        for change in patch.changes:
            if change.operation not in (
                ChangeOperation.MODIFY,
                ChangeOperation.DELETE,
                ChangeOperation.RENAME,
            ):
                continue

            path = (repository_path / change.path).resolve()

            if path.exists():
                backups[change.path] = path.read_text()

        return backups

    def _apply_changes(
        self,
        patch: Patch,
        repository_path: Path,
    ) -> list[str]:
        files_changed: list[str] = []

        for change in patch.changes:
            self._apply_change(
                change,
                repository_path,
            )

            files_changed.append(change.path)

            if change.operation == ChangeOperation.RENAME and change.new_path:
                files_changed.append(change.new_path)

        return files_changed

    def _apply_change(
        self,
        change: FileChange,
        repository_path: Path,
    ) -> None:
        path = (repository_path / change.path).resolve()

        if change.operation == ChangeOperation.CREATE:
            path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            path.write_text(
                change.new_content or "",
            )

        elif change.operation == ChangeOperation.MODIFY:
            path.write_text(
                change.new_content or "",
            )

        elif change.operation == ChangeOperation.DELETE:
            path.unlink()

        elif change.operation == ChangeOperation.RENAME:
            if not change.new_path:
                raise ValueError("Rename requires new_path")

            destination = (repository_path / change.new_path).resolve()

            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            path.rename(destination)

        else:
            raise ValueError(f"Unsupported operation: {change.operation}")

    def _restore_backups(
        self,
        backups: dict[str, str],
        repository_path: Path,
    ) -> None:
        for relative_path, content in backups.items():
            path = (repository_path / relative_path).resolve()

            path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            path.write_text(content)
