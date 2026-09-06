from __future__ import annotations

from uuid import uuid4

from app.ai.models.changes import (
    ChangeAction,
    ProposedChange,
)
from app.ai.models.critique import (
    CritiqueDecision,
    CritiqueResult,
)
from app.ai.models.execution import ExecutionResult
from app.ai.models.review import (
    ReviewResult,
    ReviewStatus,
)
from app.ai.models.summary import SummaryResult
from app.ai.workflows.graph import CodingWorkflow


class FakePlanner:
    def __init__(self):
        self.calls = 0

    def run(self, state):
        self.calls += 1

        return {
            "plan": [
                "Inspect authentication",
                "Implement JWT",
                "Add tests",
            ],
            "current_step": "planner",
            "status": "planned",
        }


class FakeRetriever:
    def __init__(self):
        self.calls = 0

    def run(self, state):
        self.calls += 1

        return {
            "retrieved_context": [],
            "current_step": "retriever",
            "status": "retrieved",
        }


class FakeCoder:
    def __init__(self):
        self.calls = 0

    def run(self, state):
        self.calls += 1

        return {
            "proposed_changes": [
                ProposedChange(
                    relative_path="app/auth/jwt.py",
                    action=ChangeAction.CREATE,
                    content="class JWTService:\n    pass",
                    reason="Add JWT authentication",
                )
            ],
            "current_step": "coder",
            "status": "coded",
        }


class FakeReviewer:
    def __init__(self):
        self.calls = 0

    def run(self, state):
        self.calls += 1

        return {
            "review_result": ReviewResult(
                status=ReviewStatus.APPROVED,
                summary="Changes look correct.",
                findings=[],
            ),
            "current_step": "reviewer",
            "status": "reviewed",
        }


class FakeCritic:
    def __init__(self, decisions):
        self.calls = 0
        self.decisions = decisions

    def run(self, state):
        decision = self.decisions[self.calls]

        self.calls += 1

        return {
            "critique": CritiqueResult(
                decision=decision,
                summary="Critic assessment.",
                findings=[],
            ),
            "current_step": "critic",
            "status": "criticized",
        }


class FakeExecutor:
    def __init__(self):
        self.calls = 0

    def run(self, state):
        self.calls += 1

        return {
            "execution_result": ExecutionResult(
                success=True,
                message="Dry run completed.",
                executed_changes=[
                    change.relative_path
                    for change in state.get(
                        "proposed_changes",
                        [],
                    )
                ],
            ),
            "current_step": "executor",
            "status": "executed",
        }


class FakeSummarizer:
    def __init__(self) -> None:
        self.calls = 0

    def run(self, state):
        self.calls += 1

        return {
            "summary": SummaryResult(summary="Workflow completed."),
            "current_step": "summarizer",
            "status": "completed",
        }


def test_workflow_executes_when_critic_approves():
    planner = FakePlanner()
    retriever = FakeRetriever()
    coder = FakeCoder()
    reviewer = FakeReviewer()

    critic = FakeCritic(
        decisions=[
            CritiqueDecision.APPROVE,
        ],
    )

    executor = FakeExecutor()

    summarizer = FakeSummarizer()

    workflow = CodingWorkflow(
        planner=planner,
        retriever=retriever,
        coder=coder,
        reviewer=reviewer,
        critic=critic,
        executor=executor,
        summarizer=summarizer,
        max_iterations=3,
    ).build()

    repository_id = uuid4()

    result = workflow.invoke(
        {
            "user_request": "Add JWT authentication",
            "repository_id": repository_id,
            "iteration_count": 0,
        }
    )

    assert planner.calls == 1
    assert retriever.calls == 1
    assert coder.calls == 1
    assert reviewer.calls == 1
    assert critic.calls == 1
    assert executor.calls == 1
    assert summarizer.calls == 1

    assert result["status"] == "completed"
    assert result["current_step"] == "summarizer"

    assert result["execution_result"].success is True

    assert result["status"] == "completed"

    assert result["summary"].summary == "Workflow completed."


def test_workflow_retries_coder_after_critic_rejection():
    planner = FakePlanner()
    retriever = FakeRetriever()
    coder = FakeCoder()
    reviewer = FakeReviewer()

    critic = FakeCritic(
        decisions=[
            CritiqueDecision.REJECT,
            CritiqueDecision.APPROVE
        ],
    )

    executor = FakeExecutor()

    summarizer = FakeSummarizer()

    workflow = CodingWorkflow(
        planner=planner,
        retriever=retriever,
        coder=coder,
        reviewer=reviewer,
        critic=critic,
        executor=executor,
        summarizer=summarizer,
        max_iterations=3,
    ).build()

    result = workflow.invoke(
        {
            "user_request": "Add JWT authentication",
            "repository_id": uuid4(),
            "iteration_count": 0,
        }
    )

    assert planner.calls == 1
    assert retriever.calls == 1

    assert coder.calls == 2
    assert reviewer.calls == 2
    assert critic.calls == 2

    assert executor.calls == 1

    assert result["status"] == "completed"
    assert result["iteration_count"] == 2

    assert summarizer.calls == 1
    assert result["iteration_count"] == 2


def test_workflow_stops_after_max_iterations():
    planner = FakePlanner()
    retriever = FakeRetriever()
    coder = FakeCoder()
    reviewer = FakeReviewer()

    critic = FakeCritic(
        decisions=[
            CritiqueDecision.REJECT,
            CritiqueDecision.REJECT,
            CritiqueDecision.REJECT,
        ],
    )

    executor = FakeExecutor()

    summarizer = FakeSummarizer()

    workflow = CodingWorkflow(
        planner=planner,
        retriever=retriever,
        coder=coder,
        reviewer=reviewer,
        critic=critic,
        executor=executor,
        summarizer=summarizer,
        max_iterations=3,
    ).build()

    result = workflow.invoke(
        {
            "user_request": "Add JWT authentication",
            "repository_id": uuid4(),
            "iteration_count": 0,
        }
    )

    assert planner.calls == 1
    assert retriever.calls == 1

    assert coder.calls == 3
    assert reviewer.calls == 3
    assert critic.calls == 3

    assert executor.calls == 0

    assert result["iteration_count"] == 3

    assert summarizer.calls == 1
    assert executor.calls == 0
    assert result["iteration_count"] == 3
