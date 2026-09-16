from pathlib import Path

from app.security.sandbox import PathSandbox
from app.tools.base import Tool, ToolContext, ToolResult
from app.tools.permissions import ToolPermission
from app.schemas.tool import DocumentationSearchArguments


DOCUMENTATION_EXTENSIONS = {
    ".md",
    ".mdx",
}


class DocumentationSearchTool(Tool):
    name = "search_documentation"
    description = "Search repository documentation for a text query."
    arguments_schema = DocumentationSearchArguments
    permission = ToolPermission.READ

    async def execute(
        self,
        arguments: dict,
        context: ToolContext,
    ) -> ToolResult:
        if not context.repository_path:
            return ToolResult(
                success=False,
                error="Repository path is required.",
            )

        query = arguments["query"].lower()
        sandbox = PathSandbox(context.repository_path)

        try:
            repository = sandbox.resolve(".")
        except PermissionError as exc:
            return ToolResult(
                success=False,
                error=str(exc),
            )

        results = []

        for path in repository.rglob("*"):
            if not path.is_file():
                continue

            if path.suffix.lower() not in DOCUMENTATION_EXTENSIONS:
                continue

            if any(
                part
                in {
                    ".git",
                    ".venv",
                    "venv",
                    "__pycache__",
                    "node_modules",
                    "dist",
                    "build",
                }
                for part in path.parts
            ):
                continue

            try:
                content = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue

            for line_number, line in enumerate(
                content.splitlines(),
                start=1,
            ):
                if query in line.lower():
                    relative_path = path.relative_to(repository)

                    results.append(
                        {
                            "path": str(relative_path),
                            "line": line_number,
                            "content": line.strip(),
                        }
                    )

        return ToolResult(
            success=True,
            output=results,
            metadata={
                "query": arguments["query"],
                "result_count": len(results),
            },
        )
