from __future__ import annotations

import uuid

from sqlalchemy import (
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel
from app.models.enums import MessageRole


class ChatMessage(BaseModel):
    """Represents a single message in a chat."""

    __tablename__ = "chat_messages"

    chat_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "chats.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    model_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    prompt_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    completion_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    total_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    message_metadata: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    chat: Mapped["Chat"] = relationship(
        back_populates="messages",
    )
