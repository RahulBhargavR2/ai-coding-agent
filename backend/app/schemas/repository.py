from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.enums import RepositoryProvider, RepositoryStatus


# -------------------------------------------------------------------------
# GitHub Import
# -------------------------------------------------------------------------


class GithubRepositoryCreate(BaseModel):
    """
    Register a GitHub repository.

    Actual cloning happens in a background workflow later.
    """

    project_id: UUID

    url: HttpUrl = Field(
        ...,
        description="GitHub repository URL.",
    )


# -------------------------------------------------------------------------
# ZIP Upload
# -------------------------------------------------------------------------


class UploadRepositoryCreate(BaseModel):
    """
    Register an uploaded repository.

    The uploaded archive will be processed later.
    """

    project_id: UUID

    name: str = Field(
        ...,
        min_length=1,
        max_length=150,
    )


# -------------------------------------------------------------------------
# Update
# -------------------------------------------------------------------------


class UpdateRepository(BaseModel):

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    default_branch: str | None = Field(
        default=None,
        max_length=100,
    )

    current_branch: str | None = Field(
        default=None,
        max_length=100,
    )

    status: RepositoryStatus | None = None


# -------------------------------------------------------------------------
# Response
# -------------------------------------------------------------------------


class RepositoryResponse(BaseModel):

    id: UUID

    project_id: UUID

    name: str

    provider: RepositoryProvider

    url: str | None

    default_branch: str

    current_branch: str

    commit_hash: str | None

    local_path: str | None

    status: RepositoryStatus

    last_indexed_at: datetime | None

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
