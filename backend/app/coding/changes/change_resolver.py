from pathlib import Path

from app.coding.changes.change import (
    ChangeOperation,
    FileChange,
)
from app.coding.changes.patch import Patch


class ChangeResolver:
    """
    Resolves repository state required to safely apply a Patch.

    In particular, MODIFY and DELETE operations need the current
    file content so PatchValidator can perform optimistic
    concurrency validation.
    """

    def resolve(
        self,
        patch: Patch,
        repository_path: Path,
    ) -> Patch:
        resolved_changes: list[FileChange] = []

        for change in patch.changes:
            path = self._safe_path(
                repository_path,
                change.path,
            )

            if change.operation == ChangeOperation.MODIFY:
                original_content = self._read_file(path)

                resolved_changes.append(
                    change.model_copy(
                        update={
                            "original_content": original_content,
                        }
                    )
                )

            elif change.operation == ChangeOperation.DELETE:
                original_content = self._read_file(path)

                resolved_changes.append(
                    change.model_copy(
                        update={
                            "original_content": original_content,
                        }
                    )
                )

            else:
                resolved_changes.append(change)

        return Patch(
            changes=resolved_changes,
            description=patch.description,
        )

    @staticmethod
    def _read_file(path: Path) -> str:
        if not path.exists():
            raise FileNotFoundError(f"File does not exist: {path}")

        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")

        return path.read_text(encoding="utf-8")

    @staticmethod
    def _safe_path(
        repository_path: Path,
        relative_path: str,
    ) -> Path:
        repository_path = repository_path.resolve()
        target = (repository_path / relative_path).resolve()

        try:
            target.relative_to(repository_path)
        except ValueError:
            raise ValueError(f"Path escapes repository: {relative_path}")

        return target
