from __future__ import annotations

import json
from typing import Any

from app.ai.llm.provider import LLMProvider
from app.ai.models.critique import (
    CritiqueDecision,
    CritiqueFinding,
    CritiqueResult,
)
from app.ai.prompts.critic import CRITIC_SYSTEM_PROMPT
from app.ai.workflows.state import CodingAgentState


class CriticAgent:
    """
    Adversarially evaluates a proposed implementation after review.
    """

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    def run(
        self,
        state: CodingAgentState,
    ) -> dict[str, Any]:
        user_prompt = self._build_prompt(state)

        response = self.llm.generate(
            system_prompt=CRITIC_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        critique = self._parse_response(response)

        return {
            "critique": critique,
            "current_step": "critic",
            "status": "criticized",
        }

    @staticmethod
    def _build_prompt(
        state: CodingAgentState,
    ) -> str:
        request = state["user_request"]

        plan = state.get(
            "plan",
            [],
        )

        context = state.get(
            "retrieved_context",
            [],
        )

        changes = state.get(
            "proposed_changes",
            [],
        )

        review = state.get(
            "review_result",
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

        review_text = ""

        if review is not None:
            findings = "\n".join(
                (
                    f"- [{finding.severity}] "
                    f"{finding.file_path}: "
                    f"{finding.message}"
                )
                for finding in review.findings
            )

            review_text = "\n".join(
                [
                    f"Status: {review.status}",
                    f"Summary: {review.summary}",
                    "Findings:",
                    findings,
                ]
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

Reviewer assessment:

{review_text}
"""

    @staticmethod
    def _parse_response(
        response: str,
    ) -> CritiqueResult:
        payload = json.loads(response)

        decision = CritiqueDecision(
            payload["decision"],
        )

        findings = [
            CritiqueFinding(
                severity=finding["severity"],
                file_path=finding["file_path"],
                message=finding["message"],
            )
            for finding in payload.get(
                "findings",
                [],
            )
        ]

        return CritiqueResult(
            decision=decision,
            summary=payload["summary"],
            findings=findings,
        )
