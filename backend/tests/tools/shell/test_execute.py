import pytest

from app.tools.base import ToolContext
from app.tools.shell.execute import ShellTool
from app.security.execution_limits import ExecutionLimits

@pytest.mark.asyncio
async def test_shell_tool_executes_allowed_command(tmp_path):
    tool = ShellTool()

    context = ToolContext(
        repository_path=str(tmp_path),
    )

    result = await tool.execute(
        arguments={
            "command": ["python", "-c", "print('hello')"],
        },
        context=context,
    )

    assert result.success is True
    assert result.output["stdout"].strip() == "hello"
    assert result.output["return_code"] == 0


@pytest.mark.asyncio
async def test_shell_tool_rejects_disallowed_command(tmp_path):
    tool = ShellTool()

    context = ToolContext(
        repository_path=str(tmp_path),
    )

    result = await tool.execute(
        arguments={
            "command": ["rm", "-rf", "."],
        },
        context=context,
    )

    assert result.success is False
    assert "Command not allowed" in result.error


@pytest.mark.asyncio
async def test_shell_tool_times_out_long_running_command(tmp_path):
    tool = ShellTool(
        execution_limits=ExecutionLimits(
            timeout_seconds=0.1,
            max_output_bytes=1_000_000,
        ),
    )

    context = ToolContext(
        repository_path=str(tmp_path),
    )

    result = await tool.execute(
        arguments={
            "command": [
                "python",
                "-c",
                "import time; time.sleep(5)",
            ],
        },
        context=context,
    )

    assert result.success is False
    assert "timed out" in result.error.lower()


@pytest.mark.asyncio
async def test_shell_tool_truncates_output(tmp_path):
    tool = ShellTool(
        execution_limits=ExecutionLimits(
            timeout_seconds=5.0,
            max_output_bytes=10,
        ),
    )

    context = ToolContext(
        repository_path=str(tmp_path),
    )

    result = await tool.execute(
        arguments={
            "command": [
                "python",
                "-c",
                "print('abcdefghijklmnopqrstuvwxyz')",
            ],
        },
        context=context,
    )

    assert result.success is True

    assert len(result.output["stdout"].encode()) <= 10
    assert result.metadata["stdout_truncated"] is True


@pytest.mark.asyncio
async def test_shell_tool_truncates_stderr(tmp_path):
    tool = ShellTool(
        execution_limits=ExecutionLimits(
            timeout_seconds=5.0,
            max_output_bytes=10,
        ),
    )

    context = ToolContext(
        repository_path=str(tmp_path),
    )

    result = await tool.execute(
        arguments={
            "command": [
                "python",
                "-c",
                "import sys; sys.stderr.write('abcdefghijklmnopqrstuvwxyz')",
            ],
        },
        context=context,
    )

    assert result.success is True
    assert len(result.output["stderr"].encode()) <= 10
    assert result.metadata["stderr_truncated"] is True


@pytest.mark.asyncio
async def test_shell_tool_cleans_up_timed_out_process(tmp_path):
    tool = ShellTool(
        execution_limits=ExecutionLimits(
            timeout_seconds=0.1,
            max_output_bytes=1_000_000,
        ),
    )

    context = ToolContext(
        repository_path=str(tmp_path),
    )

    result = await tool.execute(
        arguments={
            "command": [
                "python",
                "-c",
                "import time; time.sleep(5)",
            ],
        },
        context=context,
    )

    assert result.success is False
    assert "timed out" in result.error.lower()
