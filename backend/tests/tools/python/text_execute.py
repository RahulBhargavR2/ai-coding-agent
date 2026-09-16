import pytest

from app.tools.base import ToolContext
from app.tools.python.execute import PythonTool


@pytest.mark.asyncio
async def test_python_tool_executes_code(tmp_path):
    tool = PythonTool()

    context = ToolContext(
        repository_path=str(tmp_path),
    )

    result = await tool.execute(
        arguments={
            "code": "print(2 + 2)",
        },
        context=context,
    )

    assert result.success is True
    assert result.output["stdout"].strip() == "4"
    assert result.output["return_code"] == 0


@pytest.mark.asyncio
async def test_python_tool_uses_shell_execution_policy(tmp_path):
    tool = PythonTool()

    context = ToolContext(
        repository_path=str(tmp_path),
    )

    result = await tool.execute(
        arguments={
            "code": "print('hello')",
        },
        context=context,
    )

    assert result.success is True
    assert result.output["stdout"].strip() == "hello"
