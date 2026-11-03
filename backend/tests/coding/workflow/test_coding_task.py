from app.coding.workflow.coding_task import (
    CodingTask,
    CodingTaskStatus,
)


def test_default_task_state():
    task = CodingTask(
        task_id="task-1",
        repository_id="repo-1",
        instruction="Fix authentication",
    )

    assert task.status == CodingTaskStatus.PENDING
    assert task.iteration == 0
    assert task.max_iterations == 3
    assert task.tests_passed is False
    assert task.error is None
    assert task.can_retry is True


def test_custom_iteration_limit():
    task = CodingTask(
        task_id="task-1",
        repository_id="repo-1",
        instruction="Fix authentication",
        max_iterations=5,
    )

    assert task.max_iterations == 5
    assert task.can_retry is True


def test_task_cannot_retry_after_limit():
    task = CodingTask(
        task_id="task-1",
        repository_id="repo-1",
        instruction="Fix authentication",
        iteration=3,
        max_iterations=3,
    )

    assert task.can_retry is False


def test_task_can_retry_before_limit():
    task = CodingTask(
        task_id="task-1",
        repository_id="repo-1",
        instruction="Fix authentication",
        iteration=2,
        max_iterations=3,
    )

    assert task.can_retry is True


def test_status_can_change():
    task = CodingTask(
        task_id="task-1",
        repository_id="repo-1",
        instruction="Fix authentication",
    )

    task.status = CodingTaskStatus.CODING

    assert task.status == CodingTaskStatus.CODING


def test_completed_task():
    task = CodingTask(
        task_id="task-1",
        repository_id="repo-1",
        instruction="Fix authentication",
        status=CodingTaskStatus.COMPLETED,
        tests_passed=True,
    )

    assert task.status == CodingTaskStatus.COMPLETED
    assert task.tests_passed is True
