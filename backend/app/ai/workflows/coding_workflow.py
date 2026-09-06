from __future__ import annotations

from typing import Any

from app.ai.agents.coder import CoderAgent
from app.ai.agents.critic import CriticAgent
from app.ai.agents.executor import ExecutorAgent
from app.ai.agents.planner import PlannerAgent
from app.ai.agents.retriever import RetrieverAgent
from app.ai.agents.reviewer import ReviewerAgent
from app.ai.workflows.graph import CodingWorkflow
from app.ai.workflows.state import CodingAgentState


class CodingWorkflowService:
    """
    Application-facing service for executing the coding workflow.
    """

    def __init__(
        self,
        planner: PlannerAgent,
        retriever: RetrieverAgent,
        coder: CoderAgent,
        reviewer: ReviewerAgent,
        critic: CriticAgent,
        executor: ExecutorAgent,
        max_iterations: int = 3,
    ) -> None:
        self.workflow = CodingWorkflow(
            planner=planner,
            retriever=retriever,
            coder=coder,
            reviewer=reviewer,
            critic=critic,
            executor=executor,
            max_iterations=max_iterations,
        ).build()

    def run(
        self,
        state: CodingAgentState,
    ) -> dict[str, Any]:
        return self.workflow.invoke(
            state,
        )
