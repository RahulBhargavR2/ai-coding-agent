from typing import Any

from app.ai.llm.provider import LLMProvider
from app.ai.models.summary import SummaryResult
from app.ai.workflows.state import CodingAgentState


class SummarizerAgent:
    """
    Produces a user-facing summary of the coding workflow.
    """

    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    def run(self, state: CodingAgentState) -> dict[str, Any]:
        user_request = state["user_request"]
        plan = state.get("plan", [])
        proposed_changes = state.get("proposed_changes", [])
        review_result = state.get("review_result")
        critique = state.get("critique")
        execution_result = state.get("execution_result")

        user_prompt = f"""
User request:
{user_request}

Plan:
{plan}

Proposed changes:
{proposed_changes}

Review result:
{review_result}

Critique:
{critique}

Execution result:
{execution_result}
"""

        system_prompt = """
You are the final summarizer in an AI coding agent.

Summarize the outcome of the coding workflow for the user.

Your summary should explain:
1. What was requested.
2. What the agent planned.
3. What changes were proposed.
4. What the reviewer and critic concluded.
5. Whether the changes were executed.
6. Any important limitations or remaining issues.

Be concise and factual.

Do not claim that files were actually modified unless the execution
result explicitly says so.
"""

        response = self.llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        result = SummaryResult(summary=response)

        return {
            "summary": result,
            "current_step": "summarizer",
            "status": "completed",
        }
