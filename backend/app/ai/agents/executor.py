from __future__ import annotations

from typing import Any

from app.ai.models.execution import ExecutionResult
from app.ai.workflows.state import CodingAgentState


class ExecutorAgent:
    """
    Safely handles approved proposed changes.

    Sprint 7:
        Dry-run only.

    Future:
        Delegate actual operations to the Tool Calling system.
    """

    def run(
        self,
        state: CodingAgentState,
    ) -> dict[str, Any]:
        changes = state.get(
            "proposed_changes",
            [],
        )

        executed_changes = [change.relative_path for change in changes]

        result = ExecutionResult(
            success=True,
            message=(
                "Dry-run execution completed. " "No repository files were modified."
            ),
            executed_changes=executed_changes,
        )

        return {
            "execution_result": result,
            "current_step": "executor",
            "status": "executed",
        }
