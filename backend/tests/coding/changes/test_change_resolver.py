from pathlib import Path

from app.ai.models.changes import ChangeAction, ProposedChange
from app.coding.changes.change import ChangeOperation
from app.coding.changes.change_resolver import ChangeResolver
from app.coding.changes.patch_adapter import PatchAdapter


def test_resolves_modify_original_content(tmp_path: Path):
    file = tmp_path / "example.py"
    file.write_text("old content", encoding="utf-8")

    proposed = ProposedChange(
        relative_path="example.py",
        action=ChangeAction.MODIFY,
        content="new content",
        reason="Update file",
    )

    patch = PatchAdapter.from_proposed_changes([proposed])

    resolved = ChangeResolver().resolve(
        patch,
        tmp_path,
    )

    change = resolved.changes[0]

    assert change.operation == ChangeOperation.MODIFY
    assert change.original_content == "old content"
    assert change.new_content == "new content"


def test_resolves_delete_original_content(tmp_path: Path):
    file = tmp_path / "example.py"
    file.write_text("remove this", encoding="utf-8")

    proposed = ProposedChange(
        relative_path="example.py",
        action=ChangeAction.DELETE,
        content="remove this",
        reason="Remove file",
    )

    patch = PatchAdapter.from_proposed_changes([proposed])

    resolved = ChangeResolver().resolve(
        patch,
        tmp_path,
    )

    assert resolved.changes[0].original_content == "remove this"


def test_create_does_not_read_file(tmp_path: Path):
    proposed = ProposedChange(
        relative_path="new.py",
        action=ChangeAction.CREATE,
        content="print('hello')",
        reason="Create file",
    )

    patch = PatchAdapter.from_proposed_changes([proposed])

    resolved = ChangeResolver().resolve(
        patch,
        tmp_path,
    )

    change = resolved.changes[0]

    assert change.operation == ChangeOperation.CREATE
    assert change.original_content is None
    assert change.new_content == "print('hello')"


def test_missing_file_raises_for_modify(tmp_path: Path):
    proposed = ProposedChange(
        relative_path="missing.py",
        action=ChangeAction.MODIFY,
        content="new",
        reason="Update",
    )

    patch = PatchAdapter.from_proposed_changes([proposed])

    try:
        ChangeResolver().resolve(patch, tmp_path)
        assert False
    except FileNotFoundError:
        pass


def test_path_cannot_escape_repository(tmp_path: Path):
    proposed = ProposedChange(
        relative_path="../outside.py",
        action=ChangeAction.CREATE,
        content="bad",
        reason="Bad path",
    )

    patch = PatchAdapter.from_proposed_changes([proposed])

    try:
        ChangeResolver().resolve(patch, tmp_path)
        assert False
    except ValueError:
        pass
