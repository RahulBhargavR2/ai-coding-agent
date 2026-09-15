from uuid import UUID
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class AgentTaskRequest(BaseModel):
    repository_id: UUID
    request: str = Field(min_length=1)


class AgentExecutionResponse(BaseModel):
    success: bool
    message: str
    executed_changes: list[str]


class AgentTaskResponse(BaseModel):
    status: str
    summary: str
    execution: AgentExecutionResponse | None = None


class AgentToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_name: str = Field(min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)
