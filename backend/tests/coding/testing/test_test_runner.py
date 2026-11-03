from unittest.mock import AsyncMock

import pytest

from app.coding.testing.test_runner import TestRunner
from app.tools.base import ToolContext, ToolResult


@pytest.fixture
def context() -> ToolContext:
    return ToolContext(
        repository_path="/tmp/test-repository",
    )


@pytest.mark.asyncio
async def test_successful_test_run(context):
    tool_service = AsyncMock()

    tool_service.execute.return_value = ToolResult(
        success=True,
        output={
            "stdout": "5 passed, 1 skipped\n",
            "stderr": "",
            "return_code": 0,
        },
    )

    runner = TestRunner(
        tool_service=tool_service,
    )

    result = await runner.run(
        command=["pytest"],
        context=context,
    )

    assert result.success is True
    assert result.exit_code == 0

    assert result.stdout == "5 passed, 1 skipped\n"
    assert result.stderr == ""

    assert result.total_tests == 6
    assert result.passed_tests == 5
    assert result.skipped_tests == 1

    tool_service.execute.assert_awaited_once_with(
        tool_name="execute_command",
        arguments={
            "command": ["pytest"],
        },
        context=context,
    )


@pytest.mark.asyncio
async def test_failed_test_run(context):
    tool_service = AsyncMock()

    tool_service.execute.return_value = ToolResult(
        success=False,
        output={
            "stdout": (
                "FAILED tests/test_auth.py::test_login\n" "3 passed, 1 failed\n"
            ),
            "stderr": "",
            "return_code": 1,
        },
    )

    runner = TestRunner(
        tool_service=tool_service,
    )

    result = await runner.run(
        command=["pytest"],
        context=context,
    )

    print("hello",result)

    assert result.success is False
    assert result.exit_code == 1

    assert "tests/test_auth.py::test_login" in result.failed_tests


@pytest.mark.asyncio
async def test_command_execution_error(context):
    tool_service = AsyncMock()

    tool_service.execute.return_value = ToolResult(
        success=False,
        error="Command not allowed: pytest",
    )

    runner = TestRunner(
        tool_service=tool_service,
    )

    result = await runner.run(
        command=["pytest"],
        context=context,
    )

    assert result.success is False
    assert result.exit_code == 1
    assert result.stderr == "Command not allowed: pytest"


@pytest.mark.asyncio
async def test_timeout_error(context):
    tool_service = AsyncMock()

    tool_service.execute.return_value = ToolResult(
        success=False,
        error="Command execution timed out after 30 seconds.",
    )

    runner = TestRunner(
        tool_service=tool_service,
    )

    result = await runner.run(
        command=["pytest"],
        context=context,
    )

    assert result.success is False
    assert result.exit_code == 1
    assert "timed out" in result.stderr


@pytest.mark.asyncio
async def test_stderr_is_preserved(context):
    tool_service = AsyncMock()

    tool_service.execute.return_value = ToolResult(
        success=False,
        output={
            "stdout": "",
            "stderr": "ImportError: module not found",
            "return_code": 1,
        },
    )

    runner = TestRunner(
        tool_service=tool_service,
    )

    result = await runner.run(
        command=["pytest"],
        context=context,
    )

    assert result.success is False
    assert result.stderr == "ImportError: module not found"
