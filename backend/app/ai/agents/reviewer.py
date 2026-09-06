from __future__ import annotations

import json
from typing import Any

from app.ai.llm.provider import LLMProvider
from app.ai.models.review import (
    ReviewFinding,
    ReviewResult,
    ReviewStatus,
)
from app.ai.prompts.reviewer import REVIEWER_SYSTEM_PROMPT
from app.ai.workflows.state import CodingAgentState


class ReviewerAgent:
    """
    Reviews proposed code changes against the user request,
    implementation plan, and repository context.
    """

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    def run(
        self,
        state: CodingAgentState,
    ) -> dict[str, Any]:
        user_prompt = self._build_prompt(state)

        response = self.llm.generate(
            system_prompt=REVIEWER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        review_result = self._parse_response(response)

        return {
            "review_result": review_result,
            "current_step": "reviewer",
            "status": "reviewed",
        }

    @staticmethod
    def _build_prompt(
        state: CodingAgentState,
    ) -> str:
        request = state["user_request"]

        plan = state.get("plan", [])

        context = state.get(
            "retrieved_context",
            [],
        )

        changes = state.get(
            "proposed_changes",
            [],
        )

        plan_text = "\n".join(f"- {step}" for step in plan)

        context_parts = []

        for chunk in context:
            context_parts.append(
                "\n".join(
                    [
                        f"File: {chunk.relative_path}",
                        f"Lines: {chunk.start_line}-{chunk.end_line}",
                        f"Symbol: {chunk.symbol_name}",
                        "Content:",
                        chunk.content,
                    ]
                )
            )

        context_text = "\n\n---\n\n".join(
            context_parts,
        )

        change_parts = []

        for change in changes:
            change_parts.append(
                "\n".join(
                    [
                        f"File: {change.relative_path}",
                        f"Action: {change.action}",
                        f"Reason: {change.reason}",
                        "Proposed content:",
                        change.content,
                    ]
                )
            )

        changes_text = "\n\n---\n\n".join(
            change_parts,
        )

        return f"""
User request:

{request}

Implementation plan:

{plan_text}

Existing repository context:

{context_text}

Proposed changes:

{changes_text}
"""

    @staticmethod
    def _parse_response(
        response: str,
    ) -> ReviewResult:
        payload = json.loads(response)

        status = ReviewStatus(
            payload["status"],
        )

        findings = [
            ReviewFinding(
                severity=finding["severity"],
                file_path=finding["file_path"],
                message=finding["message"],
            )
            for finding in payload.get(
                "findings",
                [],
            )
        ]

        return ReviewResult(
            status=status,
            summary=payload["summary"],
            findings=findings,
        )
