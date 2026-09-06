from langgraph.graph import END, START, StateGraph
from typing import Any

from app.ai.agents.coder import CoderAgent
from app.ai.agents.critic import CriticAgent
from app.ai.agents.executor import ExecutorAgent
from app.ai.agents.planner import PlannerAgent
from app.ai.agents.retriever import RetrieverAgent
from app.ai.agents.reviewer import ReviewerAgent
from app.ai.agents.summarizer import SummarizerAgent
from app.ai.models.critique import CritiqueDecision
from app.ai.workflows.state import CodingAgentState


class CodingWorkflow:
    """
    LangGraph orchestration for the coding-agent workflow.
    """

    def __init__(
        self,
        planner: PlannerAgent,
        retriever: RetrieverAgent,
        coder: CoderAgent,
        reviewer: ReviewerAgent,
        critic: CriticAgent,
        executor: ExecutorAgent,
        summarizer: SummarizerAgent,
        max_iterations: int = 3,
    ) -> None:
        self.planner = planner
        self.retriever = retriever
        self.coder = coder
        self.reviewer = reviewer
        self.critic = critic
        self.executor = executor
        self.summarizer = summarizer
        self.max_iterations = max_iterations

    def build(self):
        graph = StateGraph(CodingAgentState)

        graph.add_node(
            "planner",
            self.planner.run,
        )

        graph.add_node(
            "retriever",
            self.retriever.run,
        )

        graph.add_node(
            "coder",
            self._coder_node,
        )

        graph.add_node(
            "reviewer",
            self.reviewer.run,
        )

        graph.add_node(
            "critic",
            self.critic.run,
        )

        graph.add_node(
            "executor",
            self.executor.run,
        )

        graph.add_node(
            "summarizer",
            self.summarizer.run
        )

        graph.add_edge(
            START,
            "planner",
        )

        graph.add_edge(
            "planner",
            "retriever",
        )

        graph.add_edge(
            "retriever",
            "coder",
        )

        graph.add_edge(
            "coder",
            "reviewer",
        )

        graph.add_edge(
            "reviewer",
            "critic",
        )

        graph.add_conditional_edges(
            "critic",
            self._route_after_critic,
            {
                "coder": "coder",
                "executor": "executor",
                "summarizer": "summarizer",
            },
        )

        graph.add_edge(
            "executor",
            "summarizer",
        )

        graph.add_edge(
            "summarizer",
            END
        )

        return graph.compile()

    def _coder_node(
        self,
        state: CodingAgentState,
    ) -> dict[str, Any]:
        iteration_count = state.get(
            "iteration_count",
            0,
        )

        result = self.coder.run(state)

        return {
            **result,
            "iteration_count": iteration_count + 1,
        }

    def _route_after_critic(
        self,
        state: CodingAgentState,
    ) -> str:
        critique = state["critique"]

        if critique.decision == CritiqueDecision.APPROVE:
            return "executor"

        iteration_count = state.get(
            "iteration_count",
            0,
        )

        if iteration_count >= self.max_iterations:
            return "summarizer"

        return "coder"
