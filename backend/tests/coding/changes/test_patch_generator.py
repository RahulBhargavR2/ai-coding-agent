from app.coding.changes.change import (
    ChangeOperation,
    FileChange,
)
from app.coding.changes.patch import Patch
from app.coding.changes.patch_generator import PatchGenerator


def test_generate_modify_diff():
    patch = Patch(
        changes=[
            FileChange(
                path="app/auth.py",
                operation=ChangeOperation.MODIFY,
                original_content="token = create_token(user)\n",
                new_content="token = create_access_token(user)\n",
            )
        ]
    )

    diff = PatchGenerator().generate(patch)

    assert "--- a/app/auth.py" in diff
    assert "+++ b/app/auth.py" in diff
    assert "-token = create_token(user)" in diff
    assert "+token = create_access_token(user)" in diff


def test_generate_create_diff():
    patch = Patch(
        changes=[
            FileChange(
                path="tests/test_auth.py",
                operation=ChangeOperation.CREATE,
                new_content="def test_auth():\n    assert True\n",
            )
        ]
    )

    diff = PatchGenerator().generate(patch)

    assert "--- /dev/null" in diff
    assert "+++ b/tests/test_auth.py" in diff
    assert "+def test_auth():" in diff
    assert "+    assert True" in diff


def test_generate_delete_diff():
    patch = Patch(
        changes=[
            FileChange(
                path="app/old.py",
                operation=ChangeOperation.DELETE,
                original_content="print('old')\n",
            )
        ]
    )

    diff = PatchGenerator().generate(patch)

    assert "--- a/app/old.py" in diff
    assert "+++ /dev/null" in diff
    assert "-print('old')" in diff


def test_generate_rename_diff():
    patch = Patch(
        changes=[
            FileChange(
                path="app/auth.py",
                operation=ChangeOperation.RENAME,
                original_content="auth",
                new_content="auth",
                new_path="app/security/auth.py",
            )
        ]
    )

    diff = PatchGenerator().generate(patch)

    assert "diff --git a/app/auth.py b/app/security/auth.py" in diff
    assert "rename from app/auth.py" in diff
    assert "rename to app/security/auth.py" in diff


def test_generate_empty_patch():
    patch = Patch()

    diff = PatchGenerator().generate(patch)

    assert diff == ""


def test_generate_multiple_changes():
    patch = Patch(
        changes=[
            FileChange(
                path="app/auth.py",
                operation=ChangeOperation.MODIFY,
                original_content="old\n",
                new_content="new\n",
            ),
            FileChange(
                path="tests/test_auth.py",
                operation=ChangeOperation.CREATE,
                new_content="assert True\n",
            ),
        ]
    )

    diff = PatchGenerator().generate(patch)

    assert "a/app/auth.py" in diff
    assert "b/app/auth.py" in diff
    assert "b/tests/test_auth.py" in diff
