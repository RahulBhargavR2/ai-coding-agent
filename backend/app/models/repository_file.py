from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel


class RepositoryFile(BaseModel):
    """Represents a file inside a repository."""

    __tablename__ = "repository_files"

    __table_args__ = (
        Index(
            "ix_repository_file_path",
            "repository_id",
            "relative_path",
            unique=True,
        ),
    )

    repository_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    relative_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    extension: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    language: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    size_bytes: Mapped[int] = mapped_column(
        nullable=False,
    )

    sha256_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    last_modified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    is_indexed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    is_ignored: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    repository: Mapped["Repository"] = relationship(
        back_populates="files",
    )

    embeddings: Mapped[list["Embedding"]] = relationship(
        back_populates="file",
        cascade="all, delete-orphan",
    )
