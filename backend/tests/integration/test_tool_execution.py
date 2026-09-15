import pytest

from app.ai.agents.executor import ExecutorAgent
from app.schemas.agent import AgentToolCall
from app.security.policy import CODING_POLICY
from app.tools.audit import AuditLogger
from app.tools.base import ToolContext
from app.tools.permissions import ToolPermission
from app.tools.tool_service import ToolService


@pytest.mark.asyncio
async def test_agent_tool_execution_full_pipeline(tmp_path):
    audit_logger = AuditLogger()

    tool_service = ToolService(
        audit_logger=audit_logger,
    )

    agent = ExecutorAgent(
        tool_service=tool_service,
        policy=CODING_POLICY,
    )

    context = ToolContext(
        workspace_id="workspace-1",
        repository_id="repository-1",
        repository_path=str(tmp_path),
        allowed_permissions=set(CODING_POLICY.allowed_permissions),
    )

    tool_call = AgentToolCall(
        tool_name="write_file",
        arguments={
            "path": "app/example.py",
            "content": "print('hello')",
        },
    )

    result = await agent.execute_tool_call(
        tool_call=tool_call,
        context=context,
    )

    assert result.success is True

    file_path = tmp_path / "app" / "example.py"

    assert file_path.exists()
    assert file_path.read_text(encoding="utf-8") == "print('hello')"

    records = audit_logger.get_records()

    assert len(records) == 1

    record = records[0]

    assert record.tool_name == "write_file"
    assert record.arguments == {
        "path": "app/example.py",
        "content": "print('hello')",
    }
    assert record.workspace_id == "workspace-1"
    assert record.repository_id == "repository-1"
    assert record.success is True
    assert record.error is None
