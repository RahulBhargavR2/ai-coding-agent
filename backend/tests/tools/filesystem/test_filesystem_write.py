import pytest

from app.tools.base import ToolContext
from app.tools.filesystem.write import WriteFileTool


@pytest.mark.asyncio
async def test_write_file(tmp_path):
    tool = WriteFileTool()

    context = ToolContext(
        repository_path=str(tmp_path),
    )

    result = await tool.execute(
        arguments={
            "path": "hello.txt",
            "content": "Hello, world!",
        },
        context=context,
    )

    assert result.success is True

    file_path = tmp_path / "hello.txt"

    assert file_path.exists()
    assert file_path.read_text(encoding="utf-8") == "Hello, world!"


@pytest.mark.asyncio
async def test_write_file_creates_parent_directories(tmp_path):
    tool = WriteFileTool()

    context = ToolContext(
        repository_path=str(tmp_path),
    )

    result = await tool.execute(
        arguments={
            "path": "src/utils/example.py",
            "content": "print('hello')",
        },
        context=context,
    )

    assert result.success is True

    file_path = tmp_path / "src" / "utils" / "example.py"

    assert file_path.exists()
    assert file_path.read_text(encoding="utf-8") == "print('hello')"


@pytest.mark.asyncio
async def test_write_file_rejects_path_traversal(tmp_path):
    tool = WriteFileTool()

    context = ToolContext(
        repository_path=str(tmp_path),
    )

    result = await tool.execute(
        arguments={
            "path": "../outside.txt",
            "content": "malicious",
        },
        context=context,
    )

    assert result.success is False
    assert "outside the repository sandbox" in result.error
