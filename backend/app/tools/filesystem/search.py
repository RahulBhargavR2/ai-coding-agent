from pathlib import Path

from app.tools.base import Tool, ToolContext, ToolResult
from app.security.sandbox import PathSandbox
from app.schemas.tool import SearchFilesArguments
from app.tools.permissions import ToolPermission


class SearchFilesTool(Tool):
    name = "search_files"
    description = "Search for text inside files in the repository."
    arguments_schema = SearchFilesArguments
    permission = ToolPermission.READ

    async def execute(
        self,
        arguments: dict,
        context: ToolContext,
    ) -> ToolResult:
        query = arguments.get("query")

        if not query:
            return ToolResult(
                success=False,
                error="Missing required argument: query",
            )

        if not context.repository_path:
            return ToolResult(
                success=False,
                error="Repository path is not configured.",
            )
        relative_path = arguments.get("path", ".")

        try:
            sandbox = PathSandbox(context.repository_path)
            search_path = sandbox.resolve(relative_path)
        except PermissionError as exc:
            return ToolResult(success=False, error=str(exc))


        if not search_path.exists():
            return ToolResult(
                success=False,
                error=f"Path does not exist: {relative_path}",
            )

        if not search_path.is_dir():
            return ToolResult(
                success=False,
                error=f"Path is not a directory: {relative_path}",
            )

        results = []

        try:
            files = []

            for file in search_path.rglob("*"):
                if not file.is_file():
                    continue
                
                if sandbox.is_ignored(file):
                    continue
                    
                files.append(file)

            for file in files:
                try:
                    content = file.read_text(encoding="utf-8")
                except (UnicodeDecodeError, OSError):
                    continue

                for line_number, line in enumerate(
                    content.splitlines(),
                    start=1,
                ):
                    if query in line:
                        results.append(
                            {
                                "path": str(file.relative_to(context.repository_path)),
                                "line": line_number,
                                "content": line,
                            }
                        )

        except OSError as exc:
            return ToolResult(
                success=False,
                error=f"Unable to search files: {exc}",
            )

        return ToolResult(
            success=True,
            output=results,
            metadata={
                "query": query,
                "path": relative_path,
                "count": len(results),
            },
        )
