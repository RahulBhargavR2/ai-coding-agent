import difflib

from app.coding.changes.change import ChangeOperation, FileChange
from app.coding.changes.patch import Patch


class PatchGenerator:
    """
    Converts structured FileChange objects into unified diffs.
    """

    def generate(self, patch: Patch) -> str:
        diffs: list[str] = []

        for change in patch.changes:
            diff = self._generate_change_diff(change)

            if diff:
                diffs.append(diff)

        return "\n".join(diffs)

    def _generate_change_diff(self, change: FileChange) -> str:
        if change.operation == ChangeOperation.CREATE:
            return self._create_diff(change)

        if change.operation == ChangeOperation.MODIFY:
            return self._modify_diff(change)

        if change.operation == ChangeOperation.DELETE:
            return self._delete_diff(change)

        if change.operation == ChangeOperation.RENAME:
            return self._rename_diff(change)

        raise ValueError(
            f"Unsupported change operation: {change.operation}"
        )

    def _modify_diff(self, change: FileChange) -> str:
        return self._unified_diff(
            change.original_content or "",
            change.new_content or "",
            f"a/{change.path}",
            f"b/{change.path}",
        )

    def _create_diff(self, change: FileChange) -> str:
        new_content = change.new_content or ""

        lines = new_content.splitlines(keepends=True)

        diff = difflib.unified_diff(
            [],
            lines,
            fromfile="/dev/null",
            tofile=f"b/{change.path}",
        )

        return "".join(diff)

    def _delete_diff(self, change: FileChange) -> str:
        original_content = change.original_content or ""

        lines = original_content.splitlines(keepends=True)

        diff = difflib.unified_diff(
            lines,
            [],
            fromfile=f"a/{change.path}",
            tofile="/dev/null",
        )

        return "".join(diff)

    def _rename_diff(self, change: FileChange) -> str:
        if not change.new_path:
            raise ValueError(
                "Rename operation requires new_path"
            )

        return (
            f"diff --git a/{change.path} b/{change.new_path}\n"
            f"similarity index 100%\n"
            f"rename from {change.path}\n"
            f"rename to {change.new_path}\n"
        )

    def _unified_diff(
        self,
        original: str,
        new: str,
        fromfile: str,
        tofile: str,
    ) -> str:
        original_lines = original.splitlines(keepends=True)
        new_lines = new.splitlines(keepends=True)

        return "".join(
            difflib.unified_diff(
                original_lines,
                new_lines,
                fromfile=fromfile,
                tofile=tofile,
            )
        )