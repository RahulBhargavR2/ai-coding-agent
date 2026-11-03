from app.ai.models.changes import ChangeAction, ProposedChange
from app.coding.changes.change import ChangeOperation
from app.coding.changes.patch_adapter import PatchAdapter


def test_create_change_is_converted():
    proposed = ProposedChange(
        relative_path="app/example.py",
        action=ChangeAction.CREATE,
        content="print('hello')",
        reason="Add example",
    )

    patch = PatchAdapter.from_proposed_changes(
        [proposed],
    )

    change = patch.changes[0]

    assert change.path == "app/example.py"
    assert change.operation == ChangeOperation.CREATE
    assert change.new_content == "print('hello')"


def test_modify_change_is_converted():
    proposed = ProposedChange(
        relative_path="app/example.py",
        action=ChangeAction.MODIFY,
        content="print('updated')",
        reason="Update example",
    )

    patch = PatchAdapter.from_proposed_changes(
        [proposed],
    )

    change = patch.changes[0]

    assert change.operation == ChangeOperation.MODIFY
    assert change.new_content == "print('updated')"


def test_delete_change_is_converted():
    proposed = ProposedChange(
        relative_path="app/example.py",
        action=ChangeAction.DELETE,
        content="print('old')",
        reason="Remove example",
    )

    patch = PatchAdapter.from_proposed_changes(
        [proposed],
    )

    change = patch.changes[0]

    assert change.operation == ChangeOperation.DELETE
    assert change.original_content == "print('old')"


def test_multiple_changes_are_converted():
    changes = [
        ProposedChange(
            relative_path="a.py",
            action=ChangeAction.CREATE,
            content="a",
            reason="create a",
        ),
        ProposedChange(
            relative_path="b.py",
            action=ChangeAction.CREATE,
            content="b",
            reason="create b",
        ),
    ]

    patch = PatchAdapter.from_proposed_changes(changes)

    assert patch.files_changed == 2


def test_empty_changes_create_empty_patch():
    patch = PatchAdapter.from_proposed_changes([])

    assert patch.is_empty
