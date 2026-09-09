from pathlib import Path
import pytest

from app.tools.base import ToolContext
from app.tools.filesystem.read import ReadFileTool


@pytest.mark.asyncio
async def test_read_file(tmp_path: Path):
    file_path = tmp_path / "example.py"
    file_path.write_text(
        "print('hello')",
        encoding="utf-8",
    )

    tool = ReadFileTool()

    result = await tool.execute(
        arguments={"path": "example.py"},
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is True
    assert result.output == "print('hello')"
    assert result.metadata["path"] == "example.py"


@pytest.mark.asyncio
async def test_read_missing_file(tmp_path: Path):
    tool = ReadFileTool()

    result = await tool.execute(
        arguments={"path": "missing.py"},
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is False
    assert "does not exist" in result.error


@pytest.mark.asyncio
async def test_read_directory(tmp_path: Path):
    directory = tmp_path / "app"
    directory.mkdir()

    tool = ReadFileTool()

    result = await tool.execute(
        arguments={"path": "app"},
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is False
    assert "not a file" in result.error


@pytest.mark.asyncio
async def test_read_without_repository_path():
    tool = ReadFileTool()

    result = await tool.execute(
        arguments={"path": "example.py"},
        context=ToolContext(),
    )

    assert result.success is False
    assert "Repository path" in result.error


@pytest.mark.asyncio
async def test_read_without_path(tmp_path: Path):
    tool = ReadFileTool()

    result = await tool.execute(
        arguments={},
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is False
    assert "path" in result.error


@pytest.mark.asyncio
async def test_read_file_rejects_path_traversal(tmp_path: Path):
    tool = ReadFileTool()

    result = await tool.execute(
        arguments={"path": "../../etc/passwd"},
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is False
    assert "outside the repository sandbox" in result.error


@pytest.mark.asyncio
async def test_read_file_rejects_oversized_file(tmp_path: Path):
    file_path = tmp_path / "large.txt"

    file_path.write_bytes(b"x" * (5 * 1024 * 1024 + 1))

    tool = ReadFileTool()

    result = await tool.execute(
        arguments={"path": "large.txt"},
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is False
    assert "maximum allowed size" in result.error


@pytest.mark.asyncio
async def test_read_file_rejects_symlink(tmp_path: Path):
    target = tmp_path / "secret.txt"
    target.write_text(
        "secret",
        encoding="utf-8",
    )

    link = tmp_path / "link.txt"

    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("Symlinks are not supported.")

    tool = ReadFileTool()

    result = await tool.execute(
        arguments={"path": "link.txt"},
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is False
    assert "Symlink paths are not allowed" in result.error
