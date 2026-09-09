from pathlib import Path

import pytest

from app.tools.tool_service import ToolService
from app.tools.base import Tool, ToolContext, ToolResult
from app.tools.dispatcher import ToolDispatcher
from app.tools.registry import ToolRegistry

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


@pytest.mark.asyncio
async def test_tool_service_executes_tool():
    registry = ToolRegistry()
    registry.register(FakeTool())

    dispatcher = ToolDispatcher(registry)
    service = ToolService(dispatcher)

    result = await service.execute(
        tool_name="fake_tool",
        arguments={"message": "hello"},
        context=ToolContext(),
    )

    assert result.success is True
    assert result.output == {"message": "hello"}


@pytest.mark.asyncio
async def test_tool_service_handles_unknown_tool():
    registry = ToolRegistry()

    dispatcher = ToolDispatcher(registry)
    service = ToolService(dispatcher)

    result = await service.execute(
        tool_name="unknown_tool",
        arguments={},
        context=ToolContext(),
    )

    assert result.success is False
    assert "unknown_tool" in result.error


@pytest.mark.asyncio
async def test_default_tool_service_contains_filesystem_tools(
    tmp_path: Path,
):
    service = ToolService()

    file_path = tmp_path / "example.py"
    file_path.write_text(
        "print('hello')",
        encoding="utf-8",
    )

    result = await service.execute(
        tool_name="read_file",
        arguments={"path": "example.py"},
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is True
    assert result.output == "print('hello')"


@pytest.mark.asyncio
async def test_default_tool_service_contains_git_tools(
    tmp_path: Path,
):
    service = ToolService()

    result = await service.execute(
        tool_name="git_status",
        arguments={},
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is False
    assert result.error is not None
