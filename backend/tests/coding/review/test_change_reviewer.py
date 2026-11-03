from app.coding.changes.change import (
    ChangeOperation,
    FileChange,
)
from app.coding.changes.patch import Patch
from app.coding.review.change_reviewer import (
    ChangeReviewer,
    ReviewDecision,
)


def test_valid_patch_is_approved():
    patch = Patch(
        description="Fix authentication",
        changes=[
            FileChange(
                path="app/auth.py",
                operation=ChangeOperation.MODIFY,
                original_content="old\n",
                new_content="new\n",
            )
        ],
    )

    result = ChangeReviewer().review(patch)

    assert result.decision == ReviewDecision.APPROVE
    assert result.approved is True
    assert result.issues == []


def test_empty_patch_is_rejected():
    result = ChangeReviewer().review(Patch())

    assert result.decision == ReviewDecision.REJECT
    assert result.approved is False

    assert any("no changes" in issue.message.lower() for issue in result.issues)


def test_too_many_files_are_rejected():
    changes = [
        FileChange(
            path=f"app/file_{index}.py",
            operation=ChangeOperation.CREATE,
            new_content="pass\n",
        )
        for index in range(21)
    ]

    patch = Patch(
        changes=changes,
    )

    result = ChangeReviewer().review(patch)

    assert result.decision == ReviewDecision.REJECT

    assert any("exceeding the limit" in issue.message for issue in result.issues)


def test_absolute_path_is_rejected():
    patch = Patch(
        changes=[
            FileChange(
                path="/tmp/malicious.py",
                operation=ChangeOperation.CREATE,
                new_content="pass\n",
            )
        ]
    )

    result = ChangeReviewer().review(patch)

    assert result.decision == ReviewDecision.REJECT

    assert any("Absolute path" in issue.message for issue in result.issues)


def test_path_traversal_is_rejected():
    patch = Patch(
        changes=[
            FileChange(
                path="../secret.py",
                operation=ChangeOperation.CREATE,
                new_content="pass\n",
            )
        ]
    )

    result = ChangeReviewer().review(patch)

    assert result.decision == ReviewDecision.REJECT

    assert any("Path traversal" in issue.message for issue in result.issues)


def test_nested_path_traversal_is_rejected():
    patch = Patch(
        changes=[
            FileChange(
                path="app/../../secret.py",
                operation=ChangeOperation.CREATE,
                new_content="pass\n",
            )
        ]
    )

    result = ChangeReviewer().review(patch)

    assert result.decision == ReviewDecision.REJECT


def test_sensitive_file_is_rejected():
    patch = Patch(
        changes=[
            FileChange(
                path=".env",
                operation=ChangeOperation.MODIFY,
                original_content="OLD_SECRET=x\n",
                new_content="NEW_SECRET=y\n",
            )
        ]
    )

    result = ChangeReviewer().review(patch)

    assert result.decision == ReviewDecision.REJECT

    assert any("Sensitive file" in issue.message for issue in result.issues)


def test_rename_destination_is_checked():
    patch = Patch(
        changes=[
            FileChange(
                path="app/auth.py",
                operation=ChangeOperation.RENAME,
                original_content="auth\n",
                new_content="auth\n",
                new_path="../auth.py",
            )
        ]
    )

    result = ChangeReviewer().review(patch)

    assert result.decision == ReviewDecision.REJECT

    assert any("Path traversal" in issue.message for issue in result.issues)


def test_large_patch_is_rejected():
    patch = Patch(
        changes=[
            FileChange(
                path="app/service.py",
                operation=ChangeOperation.CREATE,
                new_content="x" * 101,
            )
        ]
    )

    reviewer = ChangeReviewer(
        max_change_size=100,
    )

    result = reviewer.review(patch)

    assert result.decision == ReviewDecision.REJECT

    assert any("exceeds the limit" in issue.message for issue in result.issues)


def test_custom_file_limit():
    patch = Patch(
        changes=[
            FileChange(
                path=f"app/file_{index}.py",
                operation=ChangeOperation.CREATE,
                new_content="pass\n",
            )
            for index in range(3)
        ]
    )

    reviewer = ChangeReviewer(
        max_files=2,
    )

    result = reviewer.review(patch)

    assert result.decision == ReviewDecision.REJECT
