from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionResult:
    """
    Result of the Executor stage.

    Sprint 7 uses a safe dry-run executor.
    """

    success: bool
    message: str
    executed_changes: list[str]
