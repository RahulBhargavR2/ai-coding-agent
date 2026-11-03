import pytest
from pydantic import ValidationError

from app.coding.changes.change import (
    ChangeOperation,
    FileChange,
)
from app.coding.changes.patch import Patch


def test_empty_patch():
    patch = Patch()

    assert patch.is_empty is True
    assert patch.files_changed == 0
    assert patch.changes == []


def test_patch_with_changes():
    change = FileChange(
        path="app/auth.py",
        operation=ChangeOperation.MODIFY,
        original_content="old",
        new_content="new",
    )

    patch = Patch(
        description="Fix authentication bug",
        changes=[change],
    )

    assert patch.is_empty is False
    assert patch.files_changed == 1
    assert patch.description == "Fix authentication bug"


def test_patch_with_multiple_changes():
    changes = [
        FileChange(
            path="app/auth.py",
            operation=ChangeOperation.MODIFY,
            original_content="old",
            new_content="new",
        ),
        FileChange(
            path="tests/test_auth.py",
            operation=ChangeOperation.CREATE,
            new_content="def test_auth(): pass",
        ),
    ]

    patch = Patch(changes=changes)

    assert patch.files_changed == 2


def test_patch_rejects_duplicate_paths():
    change1 = FileChange(
        path="app/auth.py",
        operation=ChangeOperation.MODIFY,
        original_content="old",
        new_content="new",
    )

    change2 = FileChange(
        path="app/auth.py",
        operation=ChangeOperation.MODIFY,
        original_content="old2",
        new_content="new2",
    )

    with pytest.raises(ValidationError, match="Duplicate change path"):
        Patch(changes=[change1, change2])
