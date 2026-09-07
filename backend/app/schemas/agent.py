from uuid import UUID

from pydantic import BaseModel, Field


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
