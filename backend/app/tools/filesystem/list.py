from pathlib import Path

from app.tools.base import Tool, ToolContext, ToolResult
from app.security.sandbox import PathSandbox
from app.schemas.tool import ListFilesArguments


class ListFilesTool(Tool):
    name = "list_files"
    description = "List files and directories inside the repository."
    arguments_schema = ListFilesArguments

    async def execute(
        self,
        arguments: dict,
        context: ToolContext,
    ) -> ToolResult:
        if not context.repository_path:
            return ToolResult(
                success=False,
                error="Repository path is not configured.",
            )

        relative_path = arguments.get("path", ".")
        
        try:
            sandbox = PathSandbox(context.repository_path)
            directory = sandbox.resolve(relative_path)
        except PermissionError as exc:
            return ToolResult(
                success=False,
                error=str(exc)
            )


        if not directory.exists():
            return ToolResult(
                success=False,
                error=f"Directory does not exist: {relative_path}",
            )

        if not directory.is_dir():
            return ToolResult(
                success=False,
                error=f"Path is not a directory: {relative_path}",
            )

        try:
            entries = sorted(entry.name for entry in directory.iterdir())
        except OSError as exc:
            return ToolResult(
                success=False,
                error=f"Unable to list directory: {exc}",
            )

        return ToolResult(
            success=True,
            output=entries,
            metadata={
                "path": relative_path,
                "count": len(entries),
            },
        )
