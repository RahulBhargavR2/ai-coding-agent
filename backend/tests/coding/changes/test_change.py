import pytest
from pydantic import ValidationError

from app.coding.changes.change import (
    ChangeOperation,
    FileChange,
)


def test_create_change():
    change = FileChange(
        path="app/auth.py",
        operation=ChangeOperation.CREATE,
        new_content="print('hello')",
    )

    assert change.path == "app/auth.py"
    assert change.operation == ChangeOperation.CREATE
    assert change.new_content == "print('hello')"
    assert change.original_content is None


def test_modify_change():
    change = FileChange(
        path="app/auth.py",
        operation=ChangeOperation.MODIFY,
        original_content="old",
        new_content="new",
    )

    assert change.operation == ChangeOperation.MODIFY
    assert change.original_content == "old"
    assert change.new_content == "new"


def test_delete_change():
    change = FileChange(
        path="app/auth.py",
        operation=ChangeOperation.DELETE,
        original_content="old",
    )

    assert change.operation == ChangeOperation.DELETE
    assert change.original_content == "old"
    assert change.new_content is None


def test_rename_change():
    change = FileChange(
        path="app/auth.py",
        operation=ChangeOperation.RENAME,
        original_content="old",
        new_content="old",
        new_path="app/security/auth.py",
    )

    assert change.operation == ChangeOperation.RENAME
    assert change.new_path == "app/security/auth.py"


def test_create_requires_new_content():
    with pytest.raises(ValidationError):
        FileChange(
            path="app/auth.py",
            operation=ChangeOperation.CREATE,
        )


def test_create_rejects_original_content():
    with pytest.raises(ValidationError):
        FileChange(
            path="app/auth.py",
            operation=ChangeOperation.CREATE,
            original_content="old",
            new_content="new",
        )


def test_modify_requires_original_content():
    with pytest.raises(ValidationError):
        FileChange(
            path="app/auth.py",
            operation=ChangeOperation.MODIFY,
            new_content="new",
        )


def test_modify_requires_new_content():
    with pytest.raises(ValidationError):
        FileChange(
            path="app/auth.py",
            operation=ChangeOperation.MODIFY,
            original_content="old",
        )


def test_delete_requires_original_content():
    with pytest.raises(ValidationError):
        FileChange(
            path="app/auth.py",
            operation=ChangeOperation.DELETE,
        )


def test_delete_rejects_new_content():
    with pytest.raises(ValidationError):
        FileChange(
            path="app/auth.py",
            operation=ChangeOperation.DELETE,
            original_content="old",
            new_content="new",
        )


def test_rename_requires_new_path():
    with pytest.raises(ValidationError):
        FileChange(
            path="app/auth.py",
            operation=ChangeOperation.RENAME,
            original_content="old",
            new_content="old",
        )
