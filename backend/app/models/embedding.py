from __future__ import annotations

import uuid

from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel


class Embedding(BaseModel):
    """Represents an indexed text chunk."""

    __tablename__ = "embeddings"

    __table_args__ = (
        Index(
            "ix_embedding_file_chunk",
            "file_id",
            "chunk_index",
            unique=True,
        ),
    )

    file_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "repository_files.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    chunk_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    start_line: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    end_line: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    token_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    embedding_model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    vector_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    file: Mapped["RepositoryFile"] = relationship(
        back_populates="embeddings",
    )
