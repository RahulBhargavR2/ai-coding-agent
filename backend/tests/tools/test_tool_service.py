from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
import pytest

from app.tools.tool_service import ToolService
from app.tools.base import Tool, ToolContext, ToolResult
from app.tools.dispatcher import ToolDispatcher
from app.tools.registry import ToolRegistry
from app.security.permissions import PermissionChecker
from app.tools.permissions import ToolPermission
from app.tools.audit import AuditLogger


class FakeToolArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1)


class FakeTool(Tool):
    name = "fake_tool"
    description = "A fake tool used for testing."
    arguments_schema = FakeToolArguments
    permission = ToolPermission.READ

    async def execute(
        self,
        arguments: dict,
        context: ToolContext,
    ) -> ToolResult:
        return ToolResult(
            success=True,
            output=arguments,
        )


@pytest.mark.asyncio
async def test_tool_service_executes_tool():
    registry = ToolRegistry()
    registry.register(FakeTool())

    dispatcher = ToolDispatcher(registry)
    service = ToolService(dispatcher)

    result = await service.execute(
        tool_name="fake_tool",
        arguments={"message": "hello"},
        context=ToolContext(),
    )

    assert result.success is True
    assert result.output == {"message": "hello"}


@pytest.mark.asyncio
async def test_tool_service_handles_unknown_tool():
    registry = ToolRegistry()

    dispatcher = ToolDispatcher(registry)
    service = ToolService(dispatcher)

    result = await service.execute(
        tool_name="unknown_tool",
        arguments={},
        context=ToolContext(),
    )

    assert result.success is False
    assert "unknown_tool" in result.error


@pytest.mark.asyncio
async def test_default_tool_service_contains_filesystem_tools(
    tmp_path: Path,
):
    service = ToolService()

    file_path = tmp_path / "example.py"
    file_path.write_text(
        "print('hello')",
        encoding="utf-8",
    )

    result = await service.execute(
        tool_name="read_file",
        arguments={"path": "example.py"},
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is True
    assert result.output == "print('hello')"


@pytest.mark.asyncio
async def test_default_tool_service_contains_git_tools(
    tmp_path: Path,
):
    service = ToolService()

    result = await service.execute(
        tool_name="git_status",
        arguments={},
        context=ToolContext(
            repository_path=str(tmp_path),
        ),
    )

    assert result.success is False
    assert result.error is not None


def test_tool_service_returns_llm_definitions():
    service = ToolService()

    definitions = service.get_llm_definitions()

    assert len(definitions) == 7

    names = {definition["name"] for definition in definitions}

    assert names == {
        "read_file",
        "list_files",
        "write_file",
        "search_files",
        "git_status",
        "git_diff",
        "git_log",
    }


@pytest.mark.asyncio
async def test_tool_service_denies_unpermitted_tool():
    service = ToolService(
        permission_checker=PermissionChecker(allowed_permissions={ToolPermission.READ})
    )

    result = await service.execute(
        tool_name="git_status",
        arguments={},
        context=ToolContext(),
    )

    assert result.success is False
    assert result.error == "Permission denied for tool: git_status"


@pytest.mark.asyncio
async def test_tool_service_allows_permitted_tool():
    service = ToolService(
        permission_checker=PermissionChecker(allowed_permissions={ToolPermission.READ})
    )

    result = await service.execute(
        tool_name="read_file",
        arguments={"path": "test.txt"},
        context=ToolContext(),
    )

    # The tool is permitted, so execution should proceed.
    # The file itself may not exist, so we only verify
    # that the result is NOT a permission error.
    assert result.error != "Permission denied for tool: read_file"


def test_default_permissions_allow_read_and_git():
    service = ToolService()

    checker = service.permission_checker

    assert checker.is_allowed(ToolPermission.READ) is True
    assert checker.is_allowed(ToolPermission.GIT) is True


def test_default_permissions_deny_write_and_execute():
    service = ToolService()

    checker = service.permission_checker

    assert checker.is_allowed(ToolPermission.WRITE) is False
    assert checker.is_allowed(ToolPermission.EXECUTE) is False


@pytest.mark.asyncio
async def test_context_permissions_can_restrict_default_permissions():
    service = ToolService()

    result = await service.execute(
        tool_name="git_status",
        arguments={},
        context=ToolContext(allowed_permissions={ToolPermission.READ}),
    )

    assert result.success is False
    assert result.error == "Permission denied for tool: git_status"


@pytest.mark.asyncio
async def test_context_without_permissions_uses_service_defaults():
    service = ToolService()

    result = await service.execute(
        tool_name="git_status",
        arguments={},
        context=ToolContext(),
    )

    assert result.error != "Permission denied for tool: git_status"


@pytest.mark.asyncio
async def test_empty_context_permissions_deny_all_tools():
    service = ToolService()

    result = await service.execute(
        tool_name="read_file",
        arguments={"path": "test.txt"},
        context=ToolContext(allowed_permissions=set()),
    )

    assert result.success is False
    assert result.error == "Permission denied for tool: read_file"


@pytest.mark.asyncio
async def test_tool_service_audits_successful_execution(tmp_path):
    audit_logger = AuditLogger()
    service = ToolService(audit_logger=audit_logger)

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

    result = await service.execute(
        tool_name="write_file",
        arguments={
            "path": "hello.py",
            "content": "print('hello')",
        },
        context=context,
    )

    assert result.success is True

    records = audit_logger.get_records()

    assert len(records) == 1

    record = records[0]

    assert record.tool_name == "write_file"
    assert record.arguments == {
        "path": "hello.py",
        "content": "print('hello')",
    }
    assert record.workspace_id == "workspace-1"
    assert record.repository_id == "repository-1"
    assert record.success is True
    assert record.error is None


@pytest.mark.asyncio
async def test_tool_service_audits_permission_denied(tmp_path):
    audit_logger = AuditLogger()
    service = ToolService(audit_logger=audit_logger)

    context = ToolContext(
        workspace_id="workspace-1",
        repository_id="repository-1",
        repository_path=str(tmp_path),
        allowed_permissions={
            ToolPermission.READ,
            ToolPermission.GIT,
        },
    )

    result = await service.execute(
        tool_name="write_file",
        arguments={
            "path": "hello.py",
            "content": "print('hello')",
        },
        context=context,
    )

    assert result.success is False
    assert "Permission denied" in (result.error or "")

    records = audit_logger.get_records()

    assert len(records) == 1
    assert records[0].tool_name == "write_file"
    assert records[0].success is False
    assert "Permission denied" in (records[0].error or "")


@pytest.mark.asyncio
async def test_tool_service_audits_tool_failure(tmp_path):
    audit_logger = AuditLogger()
    service = ToolService(audit_logger=audit_logger)

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

    result = await service.execute(
        tool_name="read_file",
        arguments={
            "path": "does_not_exist.py",
        },
        context=context,
    )

    assert result.success is False

    records = audit_logger.get_records()

    assert len(records) == 1

    record = records[0]

    assert record.tool_name == "read_file"
    assert record.success is False
    assert record.error is not None
