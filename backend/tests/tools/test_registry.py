import pytest

from app.tools.base import Tool, ToolContext, ToolResult
from app.tools.registry import ToolRegistry
from app.core.exceptions import ToolAlreadyExists

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
            output="fake result",
        )


def test_register_and_get_tool():
    registry = ToolRegistry()
    tool = FakeTool()

    registry.register(tool)

    result = registry.get("fake_tool")

    assert result is tool


def test_register_duplicate_tool_raises():
    registry = ToolRegistry()

    registry.register(FakeTool())

    with pytest.raises(ToolAlreadyExists):
        registry.register(FakeTool())


def test_get_unknown_tool_raises():
    registry = ToolRegistry()

    with pytest.raises(KeyError):
        registry.get("unknown_tool")


def test_list_tools():
    registry = ToolRegistry()
    tool = FakeTool()

    registry.register(tool)

    tools = registry.list_tools()

    assert len(tools) == 1
    assert tools[0] is tool
