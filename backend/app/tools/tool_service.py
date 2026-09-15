from typing import Any
from datetime import datetime, timezone

from app.tools.base import ToolContext, ToolResult
from app.tools.dispatcher import ToolDispatcher
from app.tools.registry import create_default_registry
from app.security.permissions import PermissionChecker, DEFAULT_ALLOWED_PERMISSIONS

from app.tools.audit import AuditLogger, ToolAuditRecord


class ToolService:
    def __init__(
        self,
        dispatcher: ToolDispatcher | None = None,
        permission_checker: PermissionChecker | None = None,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        self.dispatcher = dispatcher or ToolDispatcher(create_default_registry())
        self.permission_checker = permission_checker or PermissionChecker(
            allowed_permissions=DEFAULT_ALLOWED_PERMISSIONS
        )

        self.audit_logger = audit_logger or AuditLogger()

    async def execute(
        self,
        tool_name: str,
        arguments: dict,
        context: ToolContext,
    ) -> ToolResult:
        try:
            tool = self.dispatcher.registry.get(tool_name)
        except KeyError as exc:
            return ToolResult(success=False, error=str(exc))

        allowed_permissions = (
            context.allowed_permissions
            if context.allowed_permissions is not None
            else self.permission_checker.allowed_permissions
        )

        if tool.permission not in allowed_permissions:
            result = ToolResult(
                success=False,
                error=f"Permission denied for tool: {tool_name}",
            )

            self.audit_logger.record(
                ToolAuditRecord(
                    tool_name=tool_name,
                    arguments=arguments,
                    workspace_id=context.workspace_id,
                    repository_id=context.repository_id,
                    success=False,
                    error=result.error,
                    timestamp=datetime.now(timezone.utc),
                )
            )

            return result
        result = await self.dispatcher.dispatch(
            tool_name=tool_name,
            arguments=arguments,
            context=context,
        )

        self.audit_logger.record(
            ToolAuditRecord(
                tool_name=tool_name,
                arguments=arguments,
                workspace_id=context.workspace_id,
                repository_id=context.repository_id,
                success=result.success,
                error=result.error,
                timestamp=datetime.now(timezone.utc),
            )
        )
        return result

    def get_llm_definitions(self) -> list[dict[str, Any]]:
        return self.dispatcher.registry.get_llm_definitions()
