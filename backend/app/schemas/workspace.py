from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from datetime import datetime
from uuid import UUID

class WorkspaceBase(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
        examples=['AI Coding Agent']
    )

    description: str | None = Field(
        default=None,
        max_length=500,
        examples=["Personal AI developemnt workspace"]
    )


class WorkspaceCreate(WorkspaceBase):
    pass


class WorkspaceUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )


class WorkspaceResponse(WorkspaceBase):
    id: UUID

    user_id: UUID

    is_default: bool

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class WorkspaceListResponse(BaseModel):
    items: list[WorkspaceResponse]

    total: int
