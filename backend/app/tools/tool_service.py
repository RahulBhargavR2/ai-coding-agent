from app.tools.base import ToolContext, ToolResult
from app.tools.dispatcher import ToolDispatcher
from app.tools.registry import create_default_registry


class ToolService:
    def __init__(
        self,
        dispatcher: ToolDispatcher | None = None,
    ) -> None:
        if dispatcher is None:
            dispatcher = ToolDispatcher(create_default_registry())

        self.dispatcher = dispatcher

    async def execute(
        self,
        tool_name: str,
        arguments: dict,
        context: ToolContext,
    ) -> ToolResult:
        return await self.dispatcher.dispatch(
            tool_name=tool_name,
            arguments=arguments,
            context=context,
        )
