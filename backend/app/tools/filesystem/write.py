from pathlib import Path

from app.security.sandbox import PathSandbox
from app.tools.base import Tool, ToolContext, ToolResult
from app.tools.permissions import ToolPermission
from app.schemas.tool import WriteFileArguments

class WriteFileTool(Tool):
    name = "write_file"
    description = "Write content to a file inside the repository"
    arguments_schema = WriteFileArguments
    permission = ToolPermission.WRITE

    async def execute(
        self,
        arguments: dict,
        context: ToolContext
    ) -> ToolResult:
        if not context.repository_path:
            return ToolResult(
                success=False,
                error="Repository path is required.",
            )

        relative_path = arguments.get('path')
        try:
            sandbox = PathSandbox(context.repository_path)
            path = sandbox.resolve(relative_path)

            path.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            path.write_text(
                arguments['content'],
                encoding='utf-8'
            )

            return ToolResult(
                success=True,
                output=f"Successfully wrote file: {relative_path}",
                metadata={
                    "path":relative_path,
                    "size":path.stat().st_size
                }
            )
        except PermissionError as exc:
            return ToolResult(
                success=False,
                error=str(exc)
            )
        except OSError as exc:
            return ToolResult(
                success=False,
                error=str(exc)
            )