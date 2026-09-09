from app.tools.base import Tool, ToolContext, ToolResult
from app.tools.dispatcher import ToolDispatcher
from app.tools.registry import ToolRegistry

from app.schemas.tool import EmptyToolArguments

import pytest

from pydantic import BaseModel, Field, ConfigDict


class FakeToolArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1)


class FakeTool(Tool):
    name = "fake_tool"
    description = "A fake tool used for testing."
    arguments_schema = FakeToolArguments

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
    arguments_schema = EmptyToolArguments

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


@pytest.mark.asyncio
async def test_dispatch_rejects_invalid_arguments():
    registry = ToolRegistry()
    registry.register(FakeTool())

    dispatcher = ToolDispatcher(registry)

    result = await dispatcher.dispatch(
        tool_name="fake_tool",
        arguments={"message": ""},
        context=ToolContext(),
    )

    assert result.success is False
    assert "Invalid tool arguments" in result.error


@pytest.mark.asyncio
async def test_dispatch_rejects_unknown_arguments():
    registry = ToolRegistry()
    registry.register(FakeTool())

    dispatcher = ToolDispatcher(registry)

    result = await dispatcher.dispatch(
        tool_name="fake_tool",
        arguments={
            "message": "hello",
            "unexpected": True,
        },
        context=ToolContext(),
    )

    assert result.success is False
    assert "Invalid tool arguments" in result.error


@pytest.mark.asyncio
async def test_dispatch_validates_argument_types():
    registry = ToolRegistry()
    registry.register(FakeTool())

    dispatcher = ToolDispatcher(registry)

    result = await dispatcher.dispatch(
        tool_name="fake_tool",
        arguments={"message": 123},
        context=ToolContext(),
    )

    assert result.success is False
    assert "Invalid tool arguments" in result.error
