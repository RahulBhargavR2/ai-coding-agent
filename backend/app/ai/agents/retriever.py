from __future__ import annotations

from typing import Any

from app.ai.workflows.state import CodingAgentState
from app.retrieval.models import RetrievalQuery, RetrievalResult
from app.retrieval.retriever import Retriever


class RetrieverAgent:
    """
    Retrieves repository context relevant to the coding request.

    The agent delegates the actual retrieval strategy to the
    injected Retriever implementation.

    For Sprint 7, this will normally be HybridRetriever.
    """

    def __init__(
        self,
        retriever: Retriever,
        limit: int = 10,
    ) -> None:
        self.retriever = retriever
        self.limit = limit

    def run(
        self,
        state: CodingAgentState,
    ) -> dict[str, Any]:
        """
        Retrieve repository context and update workflow state.
        """

        repository_id = state["repository_id"]

        query = self._build_query(state)

        retrieval_query = RetrievalQuery(
            query=query,
            repository_id=repository_id,
            limit=self.limit,
        )

        result: RetrievalResult = self.retriever.retrieve(
            retrieval_query,
        )

        return {
            "retrieved_context": result.chunks,
            "current_step": "retriever",
            "status": "retrieved",
        }

    @staticmethod
    def _build_query(
        state: CodingAgentState,
    ) -> str:
        """
        Build a repository retrieval query from the user's
        request and the Planner's implementation plan.
        """

        request = state["user_request"]

        plan = state.get("plan", [])

        parts = [
            request,
        ]

        if plan:
            parts.extend(
                [
                    "",
                    "Implementation plan:",
                ]
            )

            parts.extend(
                f"- {step}"
                for step in plan
            )

        return "\n".join(parts)