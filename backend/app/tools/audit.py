from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ToolAuditRecord:
    tool_name: str
    arguments: dict[str, Any]
    workspace_id: str | None
    repository_id: str | None
    success: bool
    error: str | None
    timestamp: datetime


class AuditLogger:
    def __init__(self) -> None:
        self.records: list[ToolAuditRecord] = []

    def record(self, audit_record: ToolAuditRecord) -> None:
        self.records.append(audit_record)

    def get_records(self) -> list[ToolAuditRecord]:
        return list(self.records)
