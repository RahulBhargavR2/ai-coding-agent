from __future__ import annotations

from typing import Any

from app.ai.models.changes import ChangeAction
from app.ai.models.execution import ExecutionResult
from app.ai.workflows.state import CodingAgentState
from app.schemas.agent import AgentToolCall
from app.tools.base import ToolContext
from app.tools.tool_service import ToolService
from app.security.policy import (READ_ONLY_POLICY, ExecutionPolicy)

class ExecutorAgent:
    def __init__(self, tool_service: ToolService, policy:ExecutionPolicy = READ_ONLY_POLICY) -> None:
        self.tool_service = tool_service
        self.policy = policy


    async def execute_tool_call(
        self,
        tool_call: AgentToolCall,
        context: ToolContext,
    ) -> ToolResult:
        return await self.tool_service.execute(
            tool_name=tool_call.tool_name,
            arguments=tool_call.arguments,
            context=context,
        )

    async def run(
        self,
        state: CodingAgentState,
    ) -> dict[str, Any]:
        changes = state.get("proposed_changes", [])

        context = ToolContext(
            workspace_id=str(state["workspace_id"]),
            repository_id=str(state["repository_id"]),
            repository_path=state["repository_path"],
            allowed_permissions=set(self.policy.allowed_permissions),
        )

        executed_changes: list[str] = []

        for change in changes:
            result = await self.execute_change(
                change=change,
                context=context,
            )

            if not result.success:
                execution = ExecutionResult(
                    success=False,
                    message=result.error or "Tool execution failed.",
                    executed_changes=executed_changes,
                )

                return {
                    "execution_result": execution,
                    "current_step": "executor",
                    "status": "failed",
                }

            executed_changes.append(change.relative_path)

        execution = ExecutionResult(
            success=True,
            message="All proposed changes were executed successfully.",
            executed_changes=executed_changes,
        )

        return {
            "execution_result": execution,
            "current_step": "executor",
            "status": "executed",
        }
