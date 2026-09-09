from pathlib import Path

import pytest

from app.tools.base import ToolContext
from app.tools.git.diff import GitDiffTool
from app.tools.git.runner import GitRunner


@pytest.mark.asyncio
async def test_git_diff_clean_repository(tmp_path: Path):
    runner = GitRunner(tmp_path)

    await runner.run("init")

    result = await GitDiffTool().execute(
        arguments={},
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is True
    assert result.output == ""


@pytest.mark.asyncio
async def test_git_diff_detects_modified_file(tmp_path: Path):
    runner = GitRunner(tmp_path)

    await runner.run("init")

    file_path = tmp_path / "example.py"

    file_path.write_text(
        "print('hello')\n",
        encoding="utf-8",
    )

    await runner.run(
        "add",
        "example.py",
    )

    await runner.run(
        "-c",
        "user.name=Test User",
        "-c",
        "user.email=test@example.com",
        "commit",
        "-m",
        "Initial commit",
    )

    file_path.write_text(
        "print('hello world')\n",
        encoding="utf-8",
    )

    result = await GitDiffTool().execute(
        arguments={},
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is True
    assert "hello world" in result.output
    assert "hello" in result.output


@pytest.mark.asyncio
async def test_git_diff_without_repository_path():
    tool = GitDiffTool()

    result = await tool.execute(
        arguments={},
        context=ToolContext(),
    )

    assert result.success is False
    assert "Repository path" in result.error


@pytest.mark.asyncio
async def test_git_diff_invalid_repository_path(tmp_path: Path):
    tool = GitDiffTool()

    missing = tmp_path / "missing"

    result = await tool.execute(
        arguments={},
        context=ToolContext(
            repository_path=str(missing),
        ),
    )

    assert result.success is False
    assert "does not exist" in result.error
