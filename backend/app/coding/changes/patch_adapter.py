from app.ai.models.changes import ProposedChange, ChangeAction
from app.coding.changes.change import ChangeOperation, FileChange
from app.coding.changes.patch import Patch


class PatchAdapter:
    """
    Converts Sprint 7 CoderAgent output into the Sprint 9 Patch model.
    """

    @staticmethod
    def from_proposed_changes(
        changes: list[ProposedChange],
    ) -> Patch:
        file_changes: list[FileChange] = []

        for change in changes:
            operation = PatchAdapter._map_operation(
                change.action,
            )

            if operation == ChangeOperation.CREATE:
                file_change = FileChange(
                    path=change.relative_path,
                    operation=operation,
                    new_content=change.content,
                )

            elif operation == ChangeOperation.MODIFY:
                file_change = FileChange(
                    path=change.relative_path,
                    operation=operation,
                    original_content="",
                    new_content=change.content,
                )

            elif operation == ChangeOperation.DELETE:
                file_change = FileChange(
                    path=change.relative_path,
                    operation=operation,
                    original_content=change.content,
                )

            else:
                raise ValueError(f"Unsupported change operation: {change.action}")

            file_changes.append(file_change)

        return Patch(
            changes=file_changes,
        )

    @staticmethod
    def _map_operation(
        action: ChangeAction,
    ) -> ChangeOperation:
        mapping = {
            ChangeAction.CREATE: ChangeOperation.CREATE,
            ChangeAction.MODIFY: ChangeOperation.MODIFY,
            ChangeAction.DELETE: ChangeOperation.DELETE,
        }

        try:
            return mapping[action]
        except KeyError:
            raise ValueError(f"Unsupported change action: {action}")
