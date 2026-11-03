from langgraph.graph import END, START, StateGraph
from typing import Any
from pathlib import Path

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
        change_reviewer: ChangeReviewer,
        change_resolver: ChangeResolver,
        editor: CodeEditor,
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
        self.change_reviewer = change_reviewer
        self.change_resolver = change_resolver
        self.editor = editor

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

        graph.add_node(
            "apply_changes",
            self._apply_changes,
        )

        graph.add_node(
            "change_review",
            self._review_changes,
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
            "change_review",
        )

        graph.add_conditional_edges(
            "change_review",
            self._route_after_change_review,
            {
                "apply_changes": "apply_changes",
                "summarizer": "summarizer",
            },
        )

        graph.add_edge(
            "apply_changes",
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

    def _review_changes(
        self,
        state: CodingAgentState,
    ) -> dict[str, Any]:
        proposed_changes = state.get(
            "proposed_changes",
            [],
        )

        patch = PatchAdapter.from_proposed_changes(
            proposed_changes,
        )

        repository_path = state["repository_path"]

        resolved_patch = self.change_resolver.resolve(
            patch,
            Path(repository_path),
        )

        review = self.change_reviewer.review(
            resolved_patch,
        )

        if not review.approved:
            return {
                "current_step": "change_review",
                "status": "rejected",
            }

        return {
            "patch":resolved_patch,
            "current_step": "change_review",
            "status": "change_reviewed",
        }


    def _route_after_change_review(
        self,
        state: CodingAgentState,
    ) -> str:
        if state.get("status") == "rejected":
            return "summarizer"

        return "apply_changes"

    async def _apply_changes(
        self,
        state: CodingAgentState,
    ) -> dict[str, Any]:
        patch = state["patch"]

        repository_path = Path(
            state["repository_path"],
        )

        result = await self.editor.apply(
            patch,
            repository_path,
        )

        if not result.success:
            return {
                "current_step": "apply_changes",
                "status": "failed",
                "execution_result": {
                    "success": False,
                    "error": result.error,
                },
            }

        return {
            "current_step": "apply_changes",
            "status": "applied",
            "execution_result": {
                "success": True,
                "files_changed": result.files_changed,
            },
        }