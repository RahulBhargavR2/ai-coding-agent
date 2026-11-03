from pathlib import Path

import pytest

from app.coding.changes.change import (
    ChangeOperation,
    FileChange,
)
from app.coding.changes.patch import Patch
from app.coding.editing.editor import CodeEditor


@pytest.fixture
def editor() -> CodeEditor:
    return CodeEditor()


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    return tmp_path


@pytest.mark.asyncio
async def test_create_file(
    editor: CodeEditor,
    repository: Path,
):
    patch = Patch(
        changes=[
            FileChange(
                path="app/auth.py",
                operation=ChangeOperation.CREATE,
                new_content="print('hello')\n",
            )
        ]
    )

    result = await editor.apply(
        patch,
        repository,
    )

    assert result.success is True
    assert result.files_changed == ["app/auth.py"]

    file = repository / "app/auth.py"

    assert file.exists()
    assert file.read_text() == "print('hello')\n"


@pytest.mark.asyncio
async def test_modify_file(
    editor: CodeEditor,
    repository: Path,
):
    file = repository / "auth.py"

    file.write_text("old content\n")

    patch = Patch(
        changes=[
            FileChange(
                path="auth.py",
                operation=ChangeOperation.MODIFY,
                original_content="old content\n",
                new_content="new content\n",
            )
        ]
    )

    result = await editor.apply(
        patch,
        repository,
    )

    assert result.success is True
    assert file.read_text() == "new content\n"


@pytest.mark.asyncio
async def test_delete_file(
    editor: CodeEditor,
    repository: Path,
):
    file = repository / "old.py"

    file.write_text("remove me\n")

    patch = Patch(
        changes=[
            FileChange(
                path="old.py",
                operation=ChangeOperation.DELETE,
                original_content="remove me\n",
            )
        ]
    )

    result = await editor.apply(
        patch,
        repository,
    )

    assert result.success is True
    assert not file.exists()


@pytest.mark.asyncio
async def test_rename_file(
    editor: CodeEditor,
    repository: Path,
):
    source = repository / "auth.py"

    source.write_text("authentication\n")

    patch = Patch(
        changes=[
            FileChange(
                path="auth.py",
                operation=ChangeOperation.RENAME,
                original_content="authentication\n",
                new_content="authentication\n",
                new_path="security/auth.py",
            )
        ]
    )

    result = await editor.apply(
        patch,
        repository,
    )

    assert result.success is True
    assert not source.exists()

    destination = repository / "security/auth.py"

    assert destination.exists()
    assert destination.read_text() == "authentication\n"


@pytest.mark.asyncio
async def test_nested_create(
    editor: CodeEditor,
    repository: Path,
):
    patch = Patch(
        changes=[
            FileChange(
                path="app/services/auth/service.py",
                operation=ChangeOperation.CREATE,
                new_content="class AuthService:\n    pass\n",
            )
        ]
    )

    result = await editor.apply(
        patch,
        repository,
    )

    assert result.success is True

    file = repository / "app/services/auth/service.py"

    assert file.exists()


@pytest.mark.asyncio
async def test_stale_file_is_not_modified(
    editor: CodeEditor,
    repository: Path,
):
    file = repository / "auth.py"

    file.write_text("user changed this\n")

    patch = Patch(
        changes=[
            FileChange(
                path="auth.py",
                operation=ChangeOperation.MODIFY,
                original_content="agent expected this\n",
                new_content="agent change\n",
            )
        ]
    )

    result = await editor.apply(
        patch,
        repository,
    )

    assert result.success is False
    assert file.read_text() == "user changed this\n"


@pytest.mark.asyncio
async def test_invalid_path_is_rejected(
    editor: CodeEditor,
    repository: Path,
):
    patch = Patch(
        changes=[
            FileChange(
                path="../outside.py",
                operation=ChangeOperation.CREATE,
                new_content="malicious\n",
            )
        ]
    )

    result = await editor.apply(
        patch,
        repository,
    )

    assert result.success is False
    assert not (repository.parent / "outside.py").exists()


@pytest.mark.asyncio
async def test_multiple_changes(
    editor: CodeEditor,
    repository: Path,
):
    auth = repository / "auth.py"
    user = repository / "user.py"

    auth.write_text("old auth\n")
    user.write_text("old user\n")

    patch = Patch(
        changes=[
            FileChange(
                path="auth.py",
                operation=ChangeOperation.MODIFY,
                original_content="old auth\n",
                new_content="new auth\n",
            ),
            FileChange(
                path="user.py",
                operation=ChangeOperation.MODIFY,
                original_content="old user\n",
                new_content="new user\n",
            ),
        ]
    )

    result = await editor.apply(
        patch,
        repository,
    )

    assert result.success is True

    assert auth.read_text() == "new auth\n"
    assert user.read_text() == "new user\n"
