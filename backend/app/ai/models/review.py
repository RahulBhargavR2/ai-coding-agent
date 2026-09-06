from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ReviewStatus(StrEnum):
    APPROVED = "approved"
    CHANGES_REQUIRED = "changes_required"


@dataclass(frozen=True)
class ReviewFinding:
    """
    A problem identified by the Reviewer.
    """

    severity: str
    file_path: str
    message: str


@dataclass(frozen=True)
class ReviewResult:
    """
    Result produced by the Reviewer agent.
    """

    status: ReviewStatus
    summary: str
    findings: list[ReviewFinding]
