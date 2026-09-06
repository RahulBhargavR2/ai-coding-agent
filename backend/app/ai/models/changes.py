from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ChangeAction(StrEnum):
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"


@dataclass(frozen=True)
class ProposedChange:
    """
    Represents a code change proposed by the Coder agent.
    """

    relative_path: str
    action: ChangeAction
    content: str
    reason: str
