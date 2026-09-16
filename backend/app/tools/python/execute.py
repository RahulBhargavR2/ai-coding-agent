from app.tools.base import Tool, ToolContext, ToolResult
from app.tools.permissions import ToolPermission
from app.schemas.tool import PythonArguments
from app.tools.shell.execute import ShellTool


class PythonTool(Tool):
    name = "execute_python"
    description = "Execute Python code inside the repository."
    arguments_schema = PythonArguments
    permission = ToolPermission.EXECUTE

    def __init__(
        self,
        shell_tool: ShellTool | None = None,
    ) -> None:
        self.shell_tool = shell_tool or ShellTool()

    async def execute(
        self,
        arguments: dict,
        context: ToolContext,
    ) -> ToolResult:
        code = arguments["code"]

        return await self.shell_tool.execute(
            arguments={
                "command": [
                    "python",
                    "-c",
                    code,
                ],
            },
            context=context,
        )
