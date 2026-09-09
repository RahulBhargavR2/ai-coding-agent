import pytest

from app.tools.base import Tool, ToolContext, ToolResult
from app.tools.registry import ToolRegistry
from app.core.exceptions import ToolAlreadyExists
from app.tools.registry import create_default_registry

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


def test_default_registry_contains_filesystem_tools():
    registry = create_default_registry()

    assert registry.get("read_file").name == "read_file"
    assert registry.get("list_files").name == "list_files"
    assert registry.get("search_files").name == "search_files"


def test_default_registry_contains_git_tools():
    registry = create_default_registry()

    assert registry.get("git_status").name == "git_status"
    assert registry.get("git_diff").name == "git_diff"
    assert registry.get("git_log").name == "git_log"


def test_default_registry_contains_all_tools():
    registry = create_default_registry()

    names = {tool.name for tool in registry.list_tools()}

    assert names == {
        "read_file",
        "list_files",
        "search_files",
        "git_status",
        "git_diff",
        "git_log",
    }


def test_tools_have_arguments_schemas():
    registry = create_default_registry()

    for tool in registry.list_tools():
        assert tool.arguments_schema is not None


def test_tool_schemas_forbid_unknown_arguments():
    registry = create_default_registry()

    read_file = registry.get("read_file")

    result = read_file.arguments_schema.model_validate({"path": "app/main.py"})

    assert result.path == "app/main.py"

import pytest


def test_read_file_schema_rejects_unknown_arguments():
    registry = create_default_registry()

    read_file = registry.get("read_file")

    with pytest.raises(Exception):
        read_file.arguments_schema.model_validate(
            {
                "path": "app/main.py",
                "unknown": True,
            }
        )
