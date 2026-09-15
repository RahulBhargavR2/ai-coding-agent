from __future__ import annotations

from typing import Any, TypedDict
from uuid import UUID

from app.retrieval.models import RetrievedChunk
from app.ai.models.changes import ProposedChange
from app.ai.models.review import ReviewResult
from app.ai.models.critique import CritiqueResult
from app.ai.models.execution import ExecutionResult
from app.ai.models.summary import SummaryResult

class CodingAgentState(TypedDict, total=False):
    """
    Shared state for the coding-agent workflow.
    """

    # Request context
    user_request: str
    workspace_id: UUID
    project_id: UUID
    repository_id: UUID
    repository_path: str

    # Planning
    plan: list[str]

    # Retrieval
    retrieved_context: list[RetrievedChunk]

    # Code generation
    proposed_changes: list[ProposedChange]

    # Validation
    review_result: ReviewResult
    critique: CritiqueResult

    # Execution
    execution_result: ExecutionResult

    # Conversation / workflow metadata
    messages: list[dict[str, Any]]
    current_step: str
    status: str

    # Control flow
    iteration_count: int

    # Summary
    summary: SummaryResult