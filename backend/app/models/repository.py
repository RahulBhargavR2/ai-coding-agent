from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel
from app.models.enums import RepositoryProvider, RepositoryStatus


class Repository(BaseModel):
    """Represents a source code repository."""

    __tablename__ = "repositories"

    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "name",
            name="uq_project_repository_name",
        ),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    provider: Mapped[RepositoryProvider] = mapped_column(
        Enum(RepositoryProvider),
        nullable=False,
    )

    url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    default_branch: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="main",
    )

    current_branch: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="main",
    )

    commit_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    local_path: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[RepositoryStatus] = mapped_column(
        Enum(RepositoryStatus),
        nullable=False,
        default=RepositoryStatus.PENDING,
    )

    last_indexed_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )

    project: Mapped["Project"] = relationship(
        back_populates="repositories",
    )

    files: Mapped[list["RepositoryFile"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
    )

    # embeddings: Mapped[list["Embedding"]] = relationship(
    #     back_populates="repository",
    #     cascade="all, delete-orphan",
    # )

    chats: Mapped[list["Chat"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
    )

