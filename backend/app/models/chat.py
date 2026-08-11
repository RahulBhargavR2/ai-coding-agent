from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from datetime import datetime

from app.models.base_model import BaseModel


class Chat(BaseModel):
    """Represents a conversation within a repository."""

    __tablename__ = "chats"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "repositories.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    last_message_at: Mapped[datetime | None]

    repository: Mapped["Repository"] = relationship(
        back_populates="chats",
    )

    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="chat",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )
