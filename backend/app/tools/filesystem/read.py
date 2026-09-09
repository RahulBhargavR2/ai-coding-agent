from pathlib import Path

from app.tools.base import Tool, ToolContext, ToolResult
from app.security.sandbox import PathSandbox

class ReadFileTool(Tool):
    name = "read_file"
    description = "Read the contents of a file from the repository."

    async def execute(
        self,
        arguments: dict,
        context: ToolContext,
    ) -> ToolResult:
        path = arguments.get("path")

        if not path:
            return ToolResult(
                success=False,
                error="Missing required argument: path",
            )

        if not context.repository_path:
            return ToolResult(
                success=False,
                error="Repository path is not configured.",
            )

        try:
            sandbox = PathSandbox(context.repository_path)
            file_path = sandbox.resolve(path)
        except PermissionError as exc:
            return ToolResult(
                success=False,
                error=str(exc)
            )

        if not file_path.exists():
            return ToolResult(
                success=False,
                error=f"File does not exist: {path}",
            )

        if not file_path.is_file():
            return ToolResult(
                success=False,
                error=f"Path is not a file: {path}",
            )
        
        try:
            sandbox.validate_file_size(file_path)
        except PermissionError as exc:
            return ToolResult(
                success=False,
                error=str(exc)
            )

        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return ToolResult(
                success=False,
                error=f"File is not valid UTF-8 text: {path}",
            )
        except OSError as exc:
            return ToolResult(
                success=False,
                error=f"Unable to read file: {exc}",
            )

        return ToolResult(
            success=True,
            output=content,
            metadata={
                "path": path,
                "size": file_path.stat().st_size,
            },
        )
