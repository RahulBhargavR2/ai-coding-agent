from __future__ import annotations

from uuid import uuid4

import pytest


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
    ReviewResult as AgentReviewResult,
    ReviewStatus,
)

from app.coding.review.change_reviewer import (
    ReviewDecision,
    ReviewResult as ChangeReviewResult,
)

from app.ai.models.summary import SummaryResult
from app.ai.workflows.graph import CodingWorkflow
from app.coding.testing.test_result import TestResult

from app.coding.testing.failure_analyzer import (
    FailureAnalysis,
    FailureAnalyzer,
)


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
            "review_result": AgentReviewResult(
                status=ReviewStatus.APPROVED,  # Use your actual enum member
                summary="Review approved.",
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


class FakeChangeReviewer:
    def __init__(self) -> None:
        self.calls = 0

    def review(self, patch):
        self.calls += 1

        return ChangeReviewResult(
            decision=ReviewDecision.APPROVE,
            issues=[],
        )


class FakeChangeResolver:
    def __init__(self) -> None:
        self.calls = 0
        self.resolved_patch = None

    def resolve(self, patch, repository_path):
        self.calls += 1
        self.resolved_patch = patch

        return patch

from app.coding.editing.editor import EditResult


class FakeCodeEditor:
    def __init__(self) -> None:
        self.calls = 0
        self.last_patch = None
        self.last_repository_path = None

    async def apply(self, patch, repository_path):
        self.calls += 1
        self.last_patch = patch
        self.last_repository_path = repository_path

        return EditResult(
            success=True,
            files_changed=len(patch.changes),
        )


class FakeTestRunner:
    def __init__(
        self,
        results: list[TestResult] | None = None,
        *,
        repeat_last: bool = False,
    ) -> None:
        self.calls = 0
        self.last_command = None
        self.last_context = None
        self.repeat_last = repeat_last

        self.results = results or [
            TestResult(
                success=True,
                exit_code=0,
                duration_ms=100,
                stdout="5 passed",
                total_tests=5,
                passed_tests=5,
                failed_tests=[],
                skipped_tests=0,
            )
        ]

    async def run(self, *, command, context):
        self.last_command = command
        self.last_context = context

        if self.calls >= len(self.results):
            if not self.repeat_last:
                raise AssertionError(
                    "FakeTestRunner received more calls than configured results."
                )

            result = self.results[-1]
        else:
            result = self.results[self.calls]

        self.calls += 1
        return result


class FakeFailureAnalyzer:
    def __init__(self) -> None:
        self.calls = 0
        self.last_test_result = None

    def analyze(self, test_result):
        self.calls += 1
        self.last_test_result = test_result

        return FailureAnalysis(
            has_failures=True,
            failures=[],
            summary="Test failures detected.",
        )


@pytest.mark.asyncio
async def test_workflow_executes_when_critic_approves():
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

    change_reviewer = FakeChangeReviewer()
    change_resolver = FakeChangeResolver()
    editor = FakeCodeEditor()
    test_runner = FakeTestRunner()
    failure_analyzer = FakeFailureAnalyzer()

    workflow = CodingWorkflow(
        planner=planner,
        retriever=retriever,
        coder=coder,
        reviewer=reviewer,
        critic=critic,
        executor=executor,
        summarizer=summarizer,
        change_reviewer=change_reviewer,
        change_resolver=change_resolver,
        editor=editor,
        test_runner=test_runner,
        failure_analyzer=failure_analyzer,
        max_iterations=3,
    ).build()

    repository_id = uuid4()

    result = await workflow.ainvoke(
        {
            "user_request": "Add JWT authentication",
            "repository_id": repository_id,
            "repository_path": "/tmp/test-repository",
            "iteration_count": 0,
            "workspace_id": uuid4(),
        }
    )

    assert planner.calls == 1
    assert retriever.calls == 1
    assert coder.calls == 1
    assert reviewer.calls == 1
    assert critic.calls == 1
    assert summarizer.calls == 1
    assert test_runner.calls == 1
    assert failure_analyzer.calls == 0
    assert result["status"] == "completed"
    assert result["current_step"] == "summarizer"


    assert result["status"] == "completed"

    assert result["summary"].summary == "Workflow completed."

@pytest.mark.asyncio
async def test_workflow_retries_coder_after_critic_rejection():
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

    change_reviewer = FakeChangeReviewer()
    change_resolver = FakeChangeResolver()
    editor = FakeCodeEditor()
    test_runner = FakeTestRunner(repeat_last=True)
    failure_analyzer = FakeFailureAnalyzer()
    workflow = CodingWorkflow(
        planner=planner,
        retriever=retriever,
        coder=coder,
        reviewer=reviewer,
        critic=critic,
        executor=executor,
        summarizer=summarizer,
        change_reviewer=change_reviewer,
        change_resolver=change_resolver,
        editor=editor,
        test_runner=test_runner,
        failure_analyzer=failure_analyzer,
        max_iterations=3,
    ).build()

    result = await workflow.ainvoke(
        {
            "user_request": "Add JWT authentication",
            "repository_id": uuid4(),
            "repository_path": "/tmp/test-repository",
            "iteration_count": 0,
            "workspace_id": uuid4(),
        }
    )

    assert planner.calls == 1
    assert retriever.calls == 1
    assert reviewer.calls == 2
    assert coder.calls == 2
    assert critic.calls == 2
    assert test_runner.calls == 2
    assert failure_analyzer.calls == 0

    assert result["status"] == "completed"
    assert result["iteration_count"] == 2

    assert summarizer.calls == 1
    assert result["iteration_count"] == 2

@pytest.mark.asyncio
async def test_workflow_stops_after_max_iterations():
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

    change_reviewer = FakeChangeReviewer()
    change_resolver = FakeChangeResolver()
    editor = FakeCodeEditor()

    test_runner = FakeTestRunner(repeat_last=True)
    failure_analyzer = FakeFailureAnalyzer()
    workflow = CodingWorkflow(
        planner=planner,
        retriever=retriever,
        coder=coder,
        reviewer=reviewer,
        critic=critic,
        executor=executor,
        summarizer=summarizer,
        change_reviewer=change_reviewer,
        change_resolver=change_resolver,
        editor=editor,
        test_runner=test_runner,
        failure_analyzer=failure_analyzer,
        max_iterations=3,
    ).build()

    result = await workflow.ainvoke(
        {
            "user_request": "Add JWT authentication",
            "repository_id": uuid4(),
            "repository_path": "/tmp/test-repository",
            "iteration_count": 0,
            "workspace_id": uuid4(),
        }
    )

    assert planner.calls == 1
    assert retriever.calls == 1

    assert coder.calls == 3
    assert reviewer.calls == 3
    assert critic.calls == 3

    assert test_runner.calls == 3
    assert failure_analyzer.calls == 0

    assert executor.calls == 0

    assert result["iteration_count"] == 3

    assert summarizer.calls == 1
    assert executor.calls == 0
    assert result["iteration_count"] == 3
