from __future__ import annotations

import json
from typing import Any

from app.ai.llm.provider import LLMProvider
from app.ai.workflows.state import CodingAgentState


class PlannerAgent:
    """
    Creates an execution plan from the user's coding request.
    """

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    def run(self, state: CodingAgentState) -> dict[str, Any]:
        user_request = state["user_request"]

        system_prompt = """
You are the Planner agent in an AI coding system.

Your responsibility is to analyze the user's coding request
and produce a clear implementation plan.

Do not modify files.
Do not execute commands.

Return a JSON object:

{
    "plan": [
        "step 1",
        "step 2"
    ]
}
"""

        user_prompt = f"""
User request:

{user_request}
"""

        response = self.llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            result = {
                "plan": [
                    response,
                ]
            }

        return {
            "plan": result["plan"],
            "current_step": "planner",
            "status": "planned",
        }
