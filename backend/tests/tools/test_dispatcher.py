from app.tools.base import Tool, ToolContext, ToolResult
from app.tools.dispatcher import ToolDispatcher
from app.tools.registry import ToolRegistry

import pytest
class FakeTool(Tool):
    name = "fake_tool"
    description = "A fake tool used for testing."

    async def execute(
        self,
        arguments: dict,
        context: ToolContext,
    ) -> ToolResult:
        return ToolResult(
            success=True,
            output=arguments,
        )


class FailingTool(Tool):
    name = "failing_tool"
    description = "A tool that fails."

    async def execute(
        self,
        arguments: dict,
        context: ToolContext,
    ) -> ToolResult:
        raise RuntimeError("Something went wrong")


@pytest.mark.asyncio
async def test_dispatch_success():
    registry = ToolRegistry()
    registry.register(FakeTool())

    dispatcher = ToolDispatcher(registry)

    context = ToolContext()

    result = await dispatcher.dispatch(
        tool_name="fake_tool",
        arguments={"message": "hello"},
        context=context,
    )

    assert result.success is True
    assert result.output == {"message": "hello"}
    assert result.error is None


@pytest.mark.asyncio
async def test_dispatch_unknown_tool():
    registry = ToolRegistry()

    dispatcher = ToolDispatcher(registry)

    result = await dispatcher.dispatch(
        tool_name="unknown_tool",
        arguments={},
        context=ToolContext(),
    )

    assert result.success is False
    assert "unknown_tool" in result.error


@pytest.mark.asyncio
async def test_dispatch_tool_failure():
    registry = ToolRegistry()
    registry.register(FailingTool())

    dispatcher = ToolDispatcher(registry)

    result = await dispatcher.dispatch(
        tool_name="failing_tool",
        arguments={},
        context=ToolContext(),
    )

    assert result.success is False
    assert result.error == "Something went wrong"
