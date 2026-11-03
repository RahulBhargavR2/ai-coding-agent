from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from app.coding.changes.change import (
    ChangeOperation,
    FileChange,
)
from app.coding.changes.patch import Patch
from app.coding.editing.editor import EditResult
from app.coding.editing.editor import CodeEditor
from app.coding.review.change_reviewer import (
    ChangeReviewer,
)
from app.coding.testing.failure_analyzer import (
    FailureAnalyzer,
)
from app.coding.testing.test_result import TestResult
from app.coding.testing.test_runner import TestRunner
from app.coding.workflow.coding_loop import CodingLoop
from app.coding.workflow.coding_task import (
    CodingTask,
    CodingTaskStatus,
)
from app.tools.base import ToolContext


@pytest.fixture
def context(tmp_path: Path) -> ToolContext:
    return ToolContext(
        repository_path=str(tmp_path),
    )


@pytest.fixture
def task() -> CodingTask:
    return CodingTask(
        task_id="task-1",
        repository_id="repo-1",
        instruction="Fix authentication",
    )


def make_patch() -> Patch:
    return Patch(
        description="Fix authentication",
        changes=[
            FileChange(
                path="auth.py",
                operation=ChangeOperation.CREATE,
                new_content="print('fixed')\n",
            )
        ],
    )


@pytest.mark.asyncio
async def test_code_test_pass_completes_task(
    task: CodingTask,
    context: ToolContext,
):
    patch_generator = AsyncMock(return_value=make_patch())

    test_command_provider = AsyncMock(return_value=["pytest"])

    editor = AsyncMock(spec=CodeEditor)

    editor.apply.return_value = EditResult(
        success=True,
        files_changed=["auth.py"],
    )

    reviewer = ChangeReviewer()

    test_runner = AsyncMock(spec=TestRunner)

    test_runner.run.return_value = TestResult(
        success=True,
        exit_code=0,
        duration_ms=100,
        stdout="5 passed\n",
        total_tests=5,
        passed_tests=5,
    )

    loop = CodingLoop(
        editor=editor,
        reviewer=reviewer,
        test_runner=test_runner,
        failure_analyzer=FailureAnalyzer(),
        patch_generator=patch_generator,
        test_command_provider=test_command_provider,
    )

    result = await loop.run(
        task,
        context,
    )

    assert result.status == CodingTaskStatus.COMPLETED
    assert result.tests_passed is True
    assert result.iteration == 1
    assert result.error is None

    patch_generator.assert_awaited_once()

    editor.apply.assert_awaited_once()

    test_runner.run.assert_awaited_once()


@pytest.mark.asyncio
async def test_code_test_fail_fix_test_pass(
    task: CodingTask,
    context: ToolContext,
):
    first_patch = make_patch()

    second_patch = Patch(
        description="Fix failed authentication test",
        changes=[
            FileChange(
                path="auth.py",
                operation=ChangeOperation.CREATE,
                new_content="print('fixed again')\n",
            )
        ],
    )

    patch_generator = AsyncMock(
        side_effect=[
            first_patch,
            second_patch,
        ]
    )

    test_command_provider = AsyncMock(return_value=["pytest"])

    editor = AsyncMock(spec=CodeEditor)

    editor.apply.return_value = EditResult(
        success=True,
        files_changed=["auth.py"],
    )

    test_runner = AsyncMock(spec=TestRunner)

    test_runner.run.side_effect = [
        TestResult(
            success=False,
            exit_code=1,
            duration_ms=100,
            stdout=(
                "FAILED tests/test_auth.py::test_login\n"
                "E   ValueError: Invalid token\n"
            ),
            failed_tests=[
                "tests/test_auth.py::test_login",
            ],
        ),
        TestResult(
            success=True,
            exit_code=0,
            duration_ms=100,
            stdout="5 passed\n",
            total_tests=5,
            passed_tests=5,
        ),
    ]

    loop = CodingLoop(
        editor=editor,
        reviewer=ChangeReviewer(),
        test_runner=test_runner,
        failure_analyzer=FailureAnalyzer(),
        patch_generator=patch_generator,
        test_command_provider=test_command_provider,
    )

    result = await loop.run(
        task,
        context,
    )

    assert result.status == CodingTaskStatus.COMPLETED
    assert result.tests_passed is True
    assert result.iteration == 2

    assert patch_generator.await_count == 2
    assert test_runner.run.await_count == 2


@pytest.mark.asyncio
async def test_max_iterations_are_enforced(
    task: CodingTask,
    context: ToolContext,
):
    task.max_iterations = 3

    patch_generator = AsyncMock(return_value=make_patch())

    test_command_provider = AsyncMock(return_value=["pytest"])

    editor = AsyncMock(spec=CodeEditor)

    editor.apply.return_value = EditResult(
        success=True,
        files_changed=["auth.py"],
    )

    test_runner = AsyncMock(spec=TestRunner)

    test_runner.run.return_value = TestResult(
        success=False,
        exit_code=1,
        duration_ms=100,
        stdout=("FAILED tests/test_auth.py::test_login\n"),
        failed_tests=[
            "tests/test_auth.py::test_login",
        ],
    )

    loop = CodingLoop(
        editor=editor,
        reviewer=ChangeReviewer(),
        test_runner=test_runner,
        failure_analyzer=FailureAnalyzer(),
        patch_generator=patch_generator,
        test_command_provider=test_command_provider,
    )

    result = await loop.run(
        task,
        context,
    )

    assert result.status == CodingTaskStatus.FAILED
    assert result.tests_passed is False
    assert result.iteration == 3

    assert patch_generator.await_count == 3
    assert test_runner.run.await_count == 3

    assert result.error == "Maximum coding iterations reached."


@pytest.mark.asyncio
async def test_reviewer_rejection_stops_execution(
    task: CodingTask,
    context: ToolContext,
):
    patch = Patch(
        changes=[
            FileChange(
                path="../secret.py",
                operation=ChangeOperation.CREATE,
                new_content="malicious\n",
            )
        ]
    )

    patch_generator = AsyncMock(return_value=patch)

    test_command_provider = AsyncMock(return_value=["pytest"])

    editor = AsyncMock(spec=CodeEditor)

    test_runner = AsyncMock(spec=TestRunner)

    loop = CodingLoop(
        editor=editor,
        reviewer=ChangeReviewer(),
        test_runner=test_runner,
        failure_analyzer=FailureAnalyzer(),
        patch_generator=patch_generator,
        test_command_provider=test_command_provider,
    )

    result = await loop.run(
        task,
        context,
    )

    assert result.status == CodingTaskStatus.REJECTED
    assert result.tests_passed is False

    editor.apply.assert_not_awaited()
    test_runner.run.assert_not_awaited()


@pytest.mark.asyncio
async def test_editor_failure_stops_execution(
    task: CodingTask,
    context: ToolContext,
):
    patch_generator = AsyncMock(return_value=make_patch())

    test_command_provider = AsyncMock(return_value=["pytest"])

    editor = AsyncMock(spec=CodeEditor)

    editor.apply.return_value = EditResult(
        success=False,
        files_changed=[],
        error="File changed since retrieval",
    )

    test_runner = AsyncMock(spec=TestRunner)

    loop = CodingLoop(
        editor=editor,
        reviewer=ChangeReviewer(),
        test_runner=test_runner,
        failure_analyzer=FailureAnalyzer(),
        patch_generator=patch_generator,
        test_command_provider=test_command_provider,
    )

    result = await loop.run(
        task,
        context,
    )

    assert result.status == CodingTaskStatus.FAILED
    assert result.error == "File changed since retrieval"

    test_runner.run.assert_not_awaited()
