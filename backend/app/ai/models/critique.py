from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CritiqueDecision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"


@dataclass(frozen=True)
class CritiqueFinding:
    """
    A concern identified by the Critic.
    """

    severity: str
    file_path: str
    message: str


@dataclass(frozen=True)
class CritiqueResult:
    """
    Result produced by the Critic agent.
    """

    decision: CritiqueDecision
    summary: str
    findings: list[CritiqueFinding]
