from app.ai.agents.executor import ExecutorAgent
from app.ai.models.changes import (
    ChangeAction,
    ProposedChange,
)
from app.ai.models.execution import ExecutionResult


def test_executor_performs_safe_dry_run():
    agent = ExecutorAgent()

    state = {
        "user_request": "Add JWT authentication",
        "proposed_changes": [
            ProposedChange(
                relative_path="app/auth/jwt.py",
                action=ChangeAction.CREATE,
                content="class JWTService:\n    pass",
                reason="Add JWT service",
            ),
            ProposedChange(
                relative_path="tests/auth/test_jwt.py",
                action=ChangeAction.CREATE,
                content="def test_jwt():\n    pass",
                reason="Add JWT tests",
            ),
        ],
    }

    result = agent.run(state)

    execution = result["execution_result"]

    assert isinstance(
        execution,
        ExecutionResult,
    )

    assert execution.success is True

    assert execution.executed_changes == [
        "app/auth/jwt.py",
        "tests/auth/test_jwt.py",
    ]

    assert "No repository files were modified" in (execution.message)

    assert result["status"] == "executed"
    assert result["current_step"] == "executor"
