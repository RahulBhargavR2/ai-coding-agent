from enum import StrEnum
from pathlib import PurePosixPath

from pydantic import BaseModel, Field

from app.coding.changes.change import ChangeOperation
from app.coding.changes.patch import Patch


class ReviewDecision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"


class ReviewIssue(BaseModel):
    message: str
    severity: str = "error"


class ReviewResult(BaseModel):
    decision: ReviewDecision
    issues: list[ReviewIssue] = Field(
        default_factory=list,
    )

    @property
    def approved(self) -> bool:
        return self.decision == ReviewDecision.APPROVE


class ChangeReviewer:
    """
    Performs deterministic safety and quality checks on a Patch.
    """

    DEFAULT_MAX_FILES = 20
    DEFAULT_MAX_CHANGE_SIZE = 100_000

    SENSITIVE_FILES = {
        ".env",
        ".env.local",
        ".env.production",
        "id_rsa",
        "id_ed25519",
    }

    def __init__(
        self,
        *,
        max_files: int = DEFAULT_MAX_FILES,
        max_change_size: int = DEFAULT_MAX_CHANGE_SIZE,
    ) -> None:
        self.max_files = max_files
        self.max_change_size = max_change_size

    def review(self, patch: Patch) -> ReviewResult:
        issues: list[ReviewIssue] = []

        self._check_empty_patch(
            patch,
            issues,
        )

        self._check_file_count(
            patch,
            issues,
        )

        self._check_paths(
            patch,
            issues,
        )

        self._check_sensitive_files(
            patch,
            issues,
        )

        self._check_change_size(
            patch,
            issues,
        )

        if issues:
            return ReviewResult(
                decision=ReviewDecision.REJECT,
                issues=issues,
            )

        return ReviewResult(
            decision=ReviewDecision.APPROVE,
        )

    @staticmethod
    def _check_empty_patch(
        patch: Patch,
        issues: list[ReviewIssue],
    ) -> None:
        if patch.is_empty:
            issues.append(
                ReviewIssue(
                    message="Patch contains no changes.",
                )
            )

    def _check_file_count(
        self,
        patch: Patch,
        issues: list[ReviewIssue],
    ) -> None:
        if patch.files_changed > self.max_files:
            issues.append(
                ReviewIssue(
                    message=(
                        f"Patch changes {patch.files_changed} files, "
                        f"exceeding the limit of {self.max_files}."
                    ),
                )
            )

    @staticmethod
    def _check_paths(
        patch: Patch,
        issues: list[ReviewIssue],
    ) -> None:
        for change in patch.changes:
            for path in (
                change.path,
                change.new_path,
            ):
                if not path:
                    continue

                pure_path = PurePosixPath(path)

                if pure_path.is_absolute():
                    issues.append(
                        ReviewIssue(
                            message=(f"Absolute path is not allowed: {path}"),
                        )
                    )
                    continue

                if ".." in pure_path.parts:
                    issues.append(
                        ReviewIssue(
                            message=(f"Path traversal is not allowed: {path}"),
                        )
                    )

    def _check_sensitive_files(
        self,
        patch: Patch,
        issues: list[ReviewIssue],
    ) -> None:
        for change in patch.changes:
            paths = [
                change.path,
            ]

            if change.new_path:
                paths.append(change.new_path)

            for path in paths:
                filename = PurePosixPath(path).name

                if filename in self.SENSITIVE_FILES:
                    issues.append(
                        ReviewIssue(
                            message=(
                                f"Sensitive file modification detected: " f"{path}"
                            ),
                            severity="warning",
                        )
                    )

    def _check_change_size(
        self,
        patch: Patch,
        issues: list[ReviewIssue],
    ) -> None:
        total_size = 0

        for change in patch.changes:
            if change.new_content:
                total_size += len(change.new_content.encode("utf-8"))

        if total_size > self.max_change_size:
            issues.append(
                ReviewIssue(
                    message=(
                        f"Patch content size ({total_size} bytes) "
                        f"exceeds the limit of "
                        f"{self.max_change_size} bytes."
                    ),
                )
            )
