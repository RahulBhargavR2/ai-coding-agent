from collections.abc import Awaitable, Callable
from typing import Any

from app.coding.changes.patch import Patch
from app.coding.editing.editor import CodeEditor
from app.coding.review.change_reviewer import (
    ChangeReviewer,
    ReviewDecision,
)
from app.coding.testing.failure_analyzer import (
    FailureAnalysis,
    FailureAnalyzer,
)
from app.coding.testing.test_result import TestResult
from app.coding.testing.test_runner import TestRunner
from app.coding.workflow.coding_task import (
    CodingTask,
    CodingTaskStatus,
)
from app.tools.base import ToolContext


PatchGeneratorCallback = Callable[
    [CodingTask, FailureAnalysis | None],
    Awaitable[Patch],
]

TestCommandCallback = Callable[
    [CodingTask],
    Awaitable[list[str]],
]


class CodingLoop:
    """
    Orchestrates the bounded code → review → edit → test → fix loop.

    Agent-specific planning, retrieval and code generation remain outside
    this class and are supplied through callbacks.
    """

    def __init__(
        self,
        *,
        editor: CodeEditor,
        reviewer: ChangeReviewer,
        test_runner: TestRunner,
        failure_analyzer: FailureAnalyzer,
        patch_generator: PatchGeneratorCallback,
        test_command_provider: TestCommandCallback,
    ) -> None:
        self.editor = editor
        self.reviewer = reviewer
        self.test_runner = test_runner
        self.failure_analyzer = failure_analyzer
        self.patch_generator = patch_generator
        self.test_command_provider = test_command_provider

    async def run(
        self,
        task: CodingTask,
        context: ToolContext,
    ) -> CodingTask:
        """
        Execute the bounded coding loop.
        """

        failure_analysis: FailureAnalysis | None = None

        while task.can_retry:
            task.iteration += 1

            task.status = CodingTaskStatus.CODING

            patch = await self.patch_generator(
                task,
                failure_analysis,
            )

            task.status = CodingTaskStatus.REVIEWING

            review = self.reviewer.review(patch)

            if review.decision == ReviewDecision.REJECT:
                task.status = CodingTaskStatus.REJECTED

                task.error = "; ".join(issue.message for issue in review.issues)

                return task

            task.status = CodingTaskStatus.APPLYING

            edit_result = await self.editor.apply(
                patch,
                self._repository_path(context),
            )

            if not edit_result.success:
                task.status = CodingTaskStatus.FAILED
                task.error = edit_result.error

                return task

            task.status = CodingTaskStatus.TESTING

            command = await self.test_command_provider(
                task,
            )

            test_result = await self.test_runner.run(
                command=command,
                context=context,
            )

            if test_result.success:
                task.status = CodingTaskStatus.COMPLETED
                task.tests_passed = True
                task.error = None

                return task

            failure_analysis = self.failure_analyzer.analyze(
                test_result,
            )

            task.status = CodingTaskStatus.ANALYZING_FAILURE

            task.tests_passed = False

        task.status = CodingTaskStatus.FAILED

        task.error = "Maximum coding iterations reached."

        return task

    @staticmethod
    def _repository_path(
        context: ToolContext,
    ):
        from pathlib import Path

        if not context.repository_path:
            raise ValueError("Repository path is required.")

        return Path(context.repository_path)
