from app.tools.base import Tool, ToolContext, ToolResult
from app.tools.git.runner import GitRunner
from app.schemas.tool import EmptyToolArguments
from app.tools.permissions import ToolPermission

class GitLogTool(Tool):
    name = "git_log"
    description = "Get the recent commit history of the repository."
    arguments_schema = EmptyToolArguments
    permission = ToolPermission.GIT

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

        try:
            runner = GitRunner(context.repository_path)
        except ValueError as exc:
            return ToolResult(
                success=False,
                error=str(exc),
            )

        result = await runner.run(
            "log",
            "--oneline",
            "-n",
            "20",
        )

        if not result.success:
            return ToolResult(
                success=False,
                error=result.stderr.strip(),
                metadata={
                    "return_code": result.return_code,
                },
            )

        return ToolResult(
            success=True,
            output=result.stdout,
            metadata={
                "return_code": result.return_code,
            },
        )
