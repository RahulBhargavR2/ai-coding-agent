from pathlib import Path

import pytest

from app.tools.base import ToolContext
from app.tools.git.log import GitLogTool
from app.tools.git.runner import GitRunner


@pytest.mark.asyncio
async def test_git_log_returns_commits(tmp_path: Path):
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

    commit = await runner.run(
        "-c",
        "user.name=Test User",
        "-c",
        "user.email=test@example.com",
        "commit",
        "-m",
        "Initial commit",
    )

    assert commit.success is True

    result = await GitLogTool().execute(
        arguments={},
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is True
    assert "Initial commit" in result.output


@pytest.mark.asyncio
async def test_git_log_limits_output_to_recent_commits(tmp_path: Path):
    runner = GitRunner(tmp_path)

    await runner.run("init")

    file_path = tmp_path / "example.txt"

    for index in range(1,26):
        file_path.write_text(
            f"version {index}\n",
            encoding="utf-8",
        )

        await runner.run(
            "add",
            "example.txt",
        )

        commit = await runner.run(
            "-c",
            "user.name=Test User",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-m",
            f"Commit {index}",
        )

        assert commit.success is True

    result = await GitLogTool().execute(
        arguments={},
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is True

    lines = [line for line in result.output.splitlines() if line.strip()]

    assert len(lines) == 20
    assert "Commit 24" in result.output
    assert "Commit 5" not in result.output


@pytest.mark.asyncio
async def test_git_log_without_repository_path():
    tool = GitLogTool()

    result = await tool.execute(
        arguments={},
        context=ToolContext(),
    )

    assert result.success is False
    assert "Repository path" in result.error


@pytest.mark.asyncio
async def test_git_log_invalid_repository_path(tmp_path: Path):
    tool = GitLogTool()

    missing = tmp_path / "missing"

    result = await tool.execute(
        arguments={},
        context=ToolContext(
            repository_path=str(missing),
        ),
    )

    assert result.success is False
    assert "does not exist" in result.error
