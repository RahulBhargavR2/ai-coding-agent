from pathlib import Path
import pytest

from app.tools.base import ToolContext
from app.tools.filesystem.search import SearchFilesTool


@pytest.mark.asyncio
async def test_search_files(tmp_path: Path):
    app_dir = tmp_path / "app"
    app_dir.mkdir()

    (app_dir / "auth.py").write_text(
        "JWT_SECRET = 'secret'\n" "def login():\n" "    pass\n",
        encoding="utf-8",
    )

    (app_dir / "user.py").write_text(
        "def get_user():\n" "    pass\n",
        encoding="utf-8",
    )

    tool = SearchFilesTool()

    result = await tool.execute(
        arguments={"query": "JWT"},
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is True
    assert result.metadata["count"] == 1

    match = result.output[0]

    assert match["path"] == "app/auth.py"
    assert match["line"] == 1
    assert "JWT_SECRET" in match["content"]


@pytest.mark.asyncio
async def test_search_subdirectory(tmp_path: Path):
    app_dir = tmp_path / "app"
    app_dir.mkdir()

    services_dir = app_dir / "services"
    services_dir.mkdir()

    (services_dir / "auth.py").write_text(
        "def authenticate():\n" "    return True\n",
        encoding="utf-8",
    )

    (app_dir / "other.py").write_text(
        "def authenticate():\n" "    return False\n",
        encoding="utf-8",
    )

    tool = SearchFilesTool()

    result = await tool.execute(
        arguments={
            "query": "authenticate",
            "path": "app/services",
        },
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is True
    assert result.metadata["count"] == 1
    assert result.output[0]["path"] == "app/services/auth.py"


@pytest.mark.asyncio
async def test_search_no_matches(tmp_path: Path):
    (tmp_path / "example.py").write_text(
        "print('hello')",
        encoding="utf-8",
    )

    tool = SearchFilesTool()

    result = await tool.execute(
        arguments={"query": "JWT"},
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is True
    assert result.output == []
    assert result.metadata["count"] == 0


@pytest.mark.asyncio
async def test_search_missing_query(tmp_path: Path):
    tool = SearchFilesTool()

    result = await tool.execute(
        arguments={},
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is False
    assert "query" in result.error


@pytest.mark.asyncio
async def test_search_without_repository_path():
    tool = SearchFilesTool()

    result = await tool.execute(
        arguments={"query": "JWT"},
        context=ToolContext(),
    )

    assert result.success is False
    assert "Repository path" in result.error


@pytest.mark.asyncio
async def test_search_missing_directory(tmp_path: Path):
    tool = SearchFilesTool()

    result = await tool.execute(
        arguments={"query": "JWT", "path": "missing"},
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is False
    assert "does not exist" in result.error


@pytest.mark.asyncio
async def test_search_files_rejects_path_traversal(tmp_path: Path):
    tool = SearchFilesTool()

    result = await tool.execute(
        arguments={
            "query": "secret",
            "path": "../../",
        },
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is False
    assert "outside the repository sandbox" in result.error


@pytest.mark.asyncio
async def test_search_files_rejects_absolute_path(tmp_path: Path):
    tool = SearchFilesTool()

    result = await tool.execute(
        arguments={
            "query": "secret",
            "path": "/etc",
        },
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is False
    assert "outside the repository sandbox" in result.error

@pytest.mark.asyncio
async def test_search_ignores_git_directory(tmp_path: Path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    (git_dir / "config").write_text(
        "SECRET_VALUE",
        encoding="utf-8",
    )

    app_dir = tmp_path / "app"
    app_dir.mkdir()

    (app_dir / "main.py").write_text(
        "print('hello')",
        encoding="utf-8",
    )

    tool = SearchFilesTool()

    result = await tool.execute(
        arguments={"query": "SECRET_VALUE"},
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is True
    assert result.output == []


@pytest.mark.asyncio
async def test_search_files_rejects_symlink(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()

    (target / "secret.txt").write_text(
        "SECRET_VALUE",
        encoding="utf-8",
    )

    link = tmp_path / "link"

    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("Symlinks are not supported.")

    tool = SearchFilesTool()

    result = await tool.execute(
        arguments={
            "query": "SECRET_VALUE",
            "path": "link",
        },
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is False
    assert "Symlink paths are not allowed" in result.error
