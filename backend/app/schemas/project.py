from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.project import ProjectStatus


class ProjectBase(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
        examples=["AI Coding Agent"],
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )

    primary_language: str | None = Field(
        default=None,
        max_length=50,
        examples=["Python"],
    )

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip()


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)

    description: str | None = Field(default=None, max_length=500)

    primary_language: str | None = Field(default=None, max_length=50)

    status: ProjectStatus | None = None


class ProjectResponse(ProjectBase):
    id: UUID

    workspace_id: UUID

    status: ProjectStatus

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]

    total: int
