from pathlib import Path
import pytest

from app.tools.base import ToolContext
from app.tools.filesystem.list import ListFilesTool


@pytest.mark.asyncio
async def test_list_files(tmp_path: Path):
    (tmp_path / "app").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "README.md").write_text(
        "# Test",
        encoding="utf-8",
    )

    tool = ListFilesTool()

    result = await tool.execute(
        arguments={},
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is True
    assert result.output == [
        "README.md",
        "app",
        "tests",
    ]
    assert result.metadata["count"] == 3


@pytest.mark.asyncio
async def test_list_subdirectory(tmp_path: Path):
    app_dir = tmp_path / "app"
    app_dir.mkdir()

    (app_dir / "main.py").write_text(
        "print('hello')",
        encoding="utf-8",
    )

    (app_dir / "config.py").write_text(
        "DEBUG = True",
        encoding="utf-8",
    )

    tool = ListFilesTool()

    result = await tool.execute(
        arguments={"path": "app"},
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is True
    assert result.output == [
        "config.py",
        "main.py",
    ]


@pytest.mark.asyncio
async def test_list_missing_directory(tmp_path: Path):
    tool = ListFilesTool()

    result = await tool.execute(
        arguments={"path": "missing"},
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is False
    assert "does not exist" in result.error


@pytest.mark.asyncio
async def test_list_file_instead_of_directory(tmp_path: Path):
    (tmp_path / "README.md").write_text(
        "# Test",
        encoding="utf-8",
    )

    tool = ListFilesTool()

    result = await tool.execute(
        arguments={"path": "README.md"},
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is False
    assert "not a directory" in result.error


@pytest.mark.asyncio
async def test_list_without_repository_path():
    tool = ListFilesTool()

    result = await tool.execute(
        arguments={},
        context=ToolContext(),
    )

    assert result.success is False
    assert "Repository path" in result.error


@pytest.mark.asyncio
async def test_list_files_rejects_path_traversal(tmp_path: Path):
    tool = ListFilesTool()

    result = await tool.execute(
        arguments={"path": "../../"},
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is False
    assert "outside the repository sandbox" in result.error


@pytest.mark.asyncio
async def test_list_files_rejects_absolute_path(tmp_path: Path):
    tool = ListFilesTool()

    result = await tool.execute(
        arguments={"path": "/etc"},
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is False
    assert "outside the repository sandbox" in result.error


@pytest.mark.asyncio
async def test_list_files_rejects_symlink(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()

    link = tmp_path / "link"

    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("Symlinks are not supported.")

    tool = ListFilesTool()

    result = await tool.execute(
        arguments={"path": "link"},
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is False
    assert "Symlink paths are not allowed" in result.error
