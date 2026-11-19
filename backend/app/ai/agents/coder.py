from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from app.ai.llm.provider import LLMProvider
from app.ai.prompts.coder import CODER_SYSTEM_PROMPT
from app.ai.workflows.state import CodingAgentState
from app.ai.models.changes import ProposedChange, ChangeAction


class CoderAgent:
    """
    Generates proposed repository changes from the user request,
    implementation plan, and retrieved repository context.
    """

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    def run(
        self,
        state: CodingAgentState,
    ) -> dict[str, Any]:
        system_prompt = CODER_SYSTEM_PROMPT

        user_prompt = self._build_prompt(state)

        response = self.llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        changes = self._parse_response(response)

        return {
            "proposed_changes": changes,
            "current_step": "coder",
            "status": "coded",
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

        failure_analysis = state.get("failure_analysis")

        failure_text = ""

        failure_text = ""

        if failure_analysis:
            failure_details = []

            for failure in failure_analysis.failures:
                detail = f"- Test: {failure.test_name}"

                if failure.file_path:
                    detail += f"\n  File: {failure.file_path}"

                if failure.line_number is not None:
                    detail += f"\n  Line: {failure.line_number}"

                if failure.error_type:
                    detail += f"\n  Error type: {failure.error_type}"

                if failure.error_message:
                    detail += f"\n  Error: {failure.error_message}"

                failure_details.append(detail)

            failure_text = f"""
        Previous test execution failed.

        Failure analysis:
        {failure_analysis.summary}

        Failure details:
        {chr(10).join(failure_details)}

        Your task is to correct the previous implementation.
        Do not blindly repeat the previous changes.
        Preserve functionality that was already working.
        """
        return f"""
            User request:

            {request}

            Implementation plan:

            {plan_text}

            Repository context:

            {context_text}

            Previous test failure analysis:

            {failure_text}
        """

    @staticmethod
    def _parse_response(
        response: str,
    ) -> list[ProposedChange]:
        payload = json.loads(response)

        changes = []

        for item in payload["changes"]:
            changes.append(
                ProposedChange(
                    relative_path=item["relative_path"],
                    action=ChangeAction(item["action"]),
                    content=item["content"],
                    reason=item["reason"],
                )
            )

        return changes
