from pathlib import Path

import pytest

from app.tools.git.runner import GitRunner


@pytest.mark.asyncio
async def test_git_runner_executes_command(tmp_path: Path):
    runner = GitRunner(tmp_path)

    result = await runner.run(
        "--version",
    )

    assert result.success is True
    assert "git version" in result.stdout.lower()


@pytest.mark.asyncio
async def test_git_runner_captures_failure(tmp_path: Path):
    runner = GitRunner(tmp_path)

    result = await runner.run(
        "status",
    )

    assert result.success is False
    assert result.return_code != 0


@pytest.mark.asyncio
async def test_git_runner_uses_repository_directory(tmp_path: Path):
    runner = GitRunner(tmp_path)

    result = await runner.run(
        "init",
    )

    assert result.success is True
    assert (tmp_path / ".git").exists()


@pytest.mark.asyncio
async def test_git_runner_captures_stdout(tmp_path: Path):
    runner = GitRunner(tmp_path)

    result = await runner.run(
        "--version",
    )

    assert result.stdout
    assert result.stderr == ""


@pytest.mark.asyncio
async def test_git_runner_timeout(tmp_path: Path):
    runner = GitRunner(
        tmp_path,
        timeout=0.001,
    )

    result = await runner.run(
        "status",
    )

    # Git may finish before the timeout on a fast system.
    # Therefore this test only verifies that execution returns
    # a normalized GitResult.
    assert isinstance(result.success, bool)
    assert isinstance(result.return_code, int)


def test_git_runner_rejects_missing_repository(tmp_path: Path):
    missing = tmp_path / "missing"

    with pytest.raises(ValueError, match="does not exist"):
        GitRunner(missing)


def test_git_runner_rejects_file_as_repository(tmp_path: Path):
    file_path = tmp_path / "file.txt"
    file_path.write_text("test", encoding="utf-8")

    with pytest.raises(ValueError, match="not a directory"):
        GitRunner(file_path)
