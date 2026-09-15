from datetime import datetime, timezone

from app.tools.audit import ToolAuditRecord, AuditLogger


def test_tool_audit_record():
    timestamp = datetime.now(timezone.utc)

    record = ToolAuditRecord(
        tool_name="write_file",
        arguments={
            "path": "hello.py",
            "content": "print('hello')",
        },
        workspace_id="workspace-1",
        repository_id="repository-1",
        success=True,
        error=None,
        timestamp=timestamp,
    )

    assert record.tool_name == "write_file"
    assert record.workspace_id == "workspace-1"
    assert record.repository_id == "repository-1"
    assert record.success is True
    assert record.error is None
    assert record.timestamp == timestamp


def test_audit_logger_records_audit_event():
    logger = AuditLogger()

    record = ToolAuditRecord(
        tool_name="write_file",
        arguments={"path": "hello.py", "content": "print('hello')"},
        workspace_id="workspace-1",
        repository_id="repository-1",
        success=True,
        error=None,
        timestamp=datetime.now(timezone.utc),
    )

    logger.record(record)

    records = logger.get_records()

    assert len(records) == 1
    assert records[0] == record


def test_audit_logger_returns_copy_of_records():
    logger = AuditLogger()

    record = ToolAuditRecord(
        tool_name="read_file",
        arguments={"path": "hello.py"},
        workspace_id="workspace-1",
        repository_id="repository-1",
        success=True,
        error=None,
        timestamp=datetime.now(timezone.utc),
    )

    logger.record(record)

    records = logger.get_records()
    records.clear()

    assert len(logger.get_records()) == 1
