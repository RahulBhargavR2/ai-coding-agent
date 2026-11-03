from pathlib import Path

import pytest

from app.coding.changes.change import (
    ChangeOperation,
    FileChange,
)
from app.coding.changes.patch import Patch
from app.coding.changes.patch_validator import (
    PatchValidationError,
    PatchValidator,
)


@pytest.fixture
def validator() -> PatchValidator:
    return PatchValidator()


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    return tmp_path


def test_create_file_is_valid(
    validator: PatchValidator,
    repository: Path,
):
    patch = Patch(
        changes=[
            FileChange(
                path="auth.py",
                operation=ChangeOperation.CREATE,
                new_content="print('hello')\n",
            )
        ]
    )

    validator.validate(patch, repository)


def test_create_existing_file_is_rejected(
    validator: PatchValidator,
    repository: Path,
):
    (repository / "auth.py").write_text("existing\n")

    patch = Patch(
        changes=[
            FileChange(
                path="auth.py",
                operation=ChangeOperation.CREATE,
                new_content="new\n",
            )
        ]
    )

    with pytest.raises(
        PatchValidationError,
        match="File already exists",
    ):
        validator.validate(patch, repository)


def test_modify_file_is_valid(
    validator: PatchValidator,
    repository: Path,
):
    original = "old content\n"

    (repository / "auth.py").write_text(original)

    patch = Patch(
        changes=[
            FileChange(
                path="auth.py",
                operation=ChangeOperation.MODIFY,
                original_content=original,
                new_content="new content\n",
            )
        ]
    )

    validator.validate(patch, repository)


def test_modify_missing_file_is_rejected(
    validator: PatchValidator,
    repository: Path,
):
    patch = Patch(
        changes=[
            FileChange(
                path="auth.py",
                operation=ChangeOperation.MODIFY,
                original_content="old\n",
                new_content="new\n",
            )
        ]
    )

    with pytest.raises(
        PatchValidationError,
        match="File does not exist",
    ):
        validator.validate(patch, repository)


def test_stale_file_is_rejected(
    validator: PatchValidator,
    repository: Path,
):
    (repository / "auth.py").write_text("user edited this\n")

    patch = Patch(
        changes=[
            FileChange(
                path="auth.py",
                operation=ChangeOperation.MODIFY,
                original_content="agent expected this\n",
                new_content="agent new content\n",
            )
        ]
    )

    with pytest.raises(
        PatchValidationError,
        match="File changed since retrieval",
    ):
        validator.validate(patch, repository)


def test_delete_file_is_valid(
    validator: PatchValidator,
    repository: Path,
):
    original = "delete me\n"

    (repository / "old.py").write_text(original)

    patch = Patch(
        changes=[
            FileChange(
                path="old.py",
                operation=ChangeOperation.DELETE,
                original_content=original,
            )
        ]
    )

    validator.validate(patch, repository)


def test_path_escape_is_rejected(
    validator: PatchValidator,
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

    with pytest.raises(
        PatchValidationError,
        match="Path escapes repository",
    ):
        validator.validate(patch, repository)


def test_absolute_path_escape_is_rejected(
    validator: PatchValidator,
    repository: Path,
):
    patch = Patch(
        changes=[
            FileChange(
                path="/tmp/outside.py",
                operation=ChangeOperation.CREATE,
                new_content="malicious\n",
            )
        ]
    )

    with pytest.raises(
        PatchValidationError,
        match="Path escapes repository",
    ):
        validator.validate(patch, repository)


def test_rename_is_valid(
    validator: PatchValidator,
    repository: Path,
):
    original = "auth code\n"

    (repository / "auth.py").write_text(original)

    patch = Patch(
        changes=[
            FileChange(
                path="auth.py",
                operation=ChangeOperation.RENAME,
                original_content=original,
                new_content=original,
                new_path="security/auth.py",
            )
        ]
    )

    validator.validate(patch, repository)


def test_rename_destination_exists_is_rejected(
    validator: PatchValidator,
    repository: Path,
):
    original = "auth code\n"

    (repository / "auth.py").write_text(original)
    (repository / "security.py").write_text("existing\n")

    patch = Patch(
        changes=[
            FileChange(
                path="auth.py",
                operation=ChangeOperation.RENAME,
                original_content=original,
                new_content=original,
                new_path="security.py",
            )
        ]
    )

    with pytest.raises(
        PatchValidationError,
        match="Destination already exists",
    ):
        validator.validate(patch, repository)
