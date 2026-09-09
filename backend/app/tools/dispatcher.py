from app.tools.base import ToolContext, ToolResult
from app.tools.registry import ToolRegistry


class ToolDispatcher:
    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry
    

    async def dispatch(
        self,
        tool_name: str,
        arguments: dict,
        context: ToolContext
    )-> ToolResult:

        try:
            tool = self.registry.get(tool_name)
        except KeyError as exc:
            return ToolResult(
                success=False,
                error=str(exc)
            )
        
        try:
            return await tool.execute(
                arguments=arguments,
                context=context
            )
        except Exception as exc:
            return ToolResult(
                success=False,
                error=str(exc)
            )
