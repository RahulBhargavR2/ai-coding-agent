from pathlib import Path

import pytest

from app.tools.base import ToolContext
from app.tools.git.status import GitStatusTool
from app.tools.git.runner import GitRunner


@pytest.mark.asyncio
async def test_git_status_clean_repository(tmp_path: Path):
    tool = GitStatusTool()

    runner = GitRunner(tmp_path)

    await runner.run("init")

    result = await tool.execute(
        arguments={},
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is True
    assert result.output == ""


@pytest.mark.asyncio
async def test_git_status_detects_untracked_file(tmp_path: Path):
    runner = __import__(
        "app.tools.git.runner",
        fromlist=["GitRunner"],
    ).GitRunner(tmp_path)

    await runner.run("init")

    file_path = tmp_path / "example.py"
    file_path.write_text(
        "print('hello')",
        encoding="utf-8",
    )

    tool = GitStatusTool()

    result = await tool.execute(
        arguments={},
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is True
    assert "example.py" in result.output


@pytest.mark.asyncio
async def test_git_status_without_repository_path():
    tool = GitStatusTool()

    result = await tool.execute(
        arguments={},
        context=ToolContext(),
    )

    assert result.success is False
    assert "Repository path" in result.error


@pytest.mark.asyncio
async def test_git_status_invalid_repository_path(tmp_path: Path):
    tool = GitStatusTool()

    missing = tmp_path / "missing"

    result = await tool.execute(
        arguments={},
        context=ToolContext(
            repository_path=str(missing),
        ),
    )

    assert result.success is False
    assert "does not exist" in result.error
