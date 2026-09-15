
import pytest

from app.ai.agents.executor import ExecutorAgent
from app.ai.models.execution import ExecutionResult
from app.schemas.agent import AgentToolCall
from app.security.policy import CODING_POLICY, READ_ONLY_POLICY
from app.tools.base import ToolContext, ToolResult
from app.tools.permissions import ToolPermission
from app.tools.tool_service import ToolService


class FakeToolService:
    def __init__(self):
        self.calls = []

    async def execute(
        self,
        tool_name,
        arguments,
        context,
    ):
        self.calls.append(
            {
                "tool_name": tool_name,
                "arguments": arguments,
                "context": context,
            }
        )

        return ToolResult(
            success=True,
            output="written",
        )


@pytest.mark.asyncio
async def test_executor_executes_tool_call():
    tool_service = FakeToolService()

    agent = ExecutorAgent(
        tool_service=tool_service,
        policy=CODING_POLICY,
    )

    context = ToolContext(
        workspace_id="workspace-1",
        repository_id="repository-1",
        repository_path="/tmp/repository",
        allowed_permissions={
            ToolPermission.READ,
            ToolPermission.GIT,
            ToolPermission.WRITE,
        },
    )

    tool_call = AgentToolCall(
        tool_name="write_file",
        arguments={
            "path": "app/auth/jwt.py",
            "content": "class JWTService:\n    pass",
        },
    )

    result = await agent.execute_tool_call(
        tool_call=tool_call,
        context=context,
    )

    assert result.success is True
    assert result.output == "written"

    assert len(tool_service.calls) == 1

    assert tool_service.calls[0]["tool_name"] == "write_file"

    assert tool_service.calls[0]["arguments"] == {
        "path": "app/auth/jwt.py",
        "content": "class JWTService:\n    pass",
    }

    assert tool_service.calls[0]["context"] is context


@pytest.mark.asyncio
async def test_executor_executes_real_tool_call(tmp_path):
    tool_service = ToolService()

    agent = ExecutorAgent(
        tool_service=tool_service,
        policy=CODING_POLICY,
    )

    context = ToolContext(
        workspace_id="workspace-1",
        repository_id="repository-1",
        repository_path=str(tmp_path),
        allowed_permissions={
            ToolPermission.READ,
            ToolPermission.GIT,
            ToolPermission.WRITE,
        },
    )

    tool_call = AgentToolCall(
        tool_name="write_file",
        arguments={
            "path": "hello.py",
            "content": "print('hello')",
        },
    )

    result = await agent.execute_tool_call(
        tool_call=tool_call,
        context=context,
    )

    assert result.success is True

    file_path = tmp_path / "hello.py"

    assert file_path.exists()
    assert file_path.read_text(encoding="utf-8") == "print('hello')"


@pytest.mark.asyncio
async def test_executor_respects_read_only_policy(tmp_path):
    tool_service = ToolService()

    agent = ExecutorAgent(
        tool_service=tool_service,
        policy=READ_ONLY_POLICY,
    )

    context = ToolContext(
        workspace_id="workspace-1",
        repository_id="repository-1",
        repository_path=str(tmp_path),
        allowed_permissions={
            ToolPermission.READ,
            ToolPermission.GIT,
        },
    )

    tool_call = AgentToolCall(
        tool_name="write_file",
        arguments={
            "path": "hello.py",
            "content": "print('hello')",
        },
    )

    result = await agent.execute_tool_call(
        tool_call=tool_call,
        context=context,
    )

    assert result.success is False
    assert "Permission denied" in (result.error or "")

    assert not (tmp_path / "hello.py").exists()


@pytest.mark.asyncio
async def test_executor_run_returns_execution_result():
    tool_service = FakeToolService()

    agent = ExecutorAgent(
        tool_service=tool_service,
        policy=READ_ONLY_POLICY,
    )

    state = {
        "user_request": "No changes",
        "workspace_id": "workspace-1",
        "repository_id": "repository-1",
        "repository_path": "/tmp/repository",
        "proposed_changes": [],
    }

    result = await agent.run(state)

    execution = result["execution_result"]

    assert isinstance(execution, ExecutionResult)
    assert execution.success is True
    assert execution.executed_changes == []
    assert result["status"] == "executed"
    assert result["current_step"] == "executor"

