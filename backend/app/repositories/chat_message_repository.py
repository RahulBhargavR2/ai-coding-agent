from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chat_message import ChatMessage
from app.repositories.base_repository import BaseRepository


class ChatMessageRepository(BaseRepository[ChatMessage]):
    """
    Handles persistence operations for chat messages.
    """

    def __init__(self, db: Session) -> None:
        super().__init__(
            db,
            ChatMessage,
        )

    def create(
        self,
        message: ChatMessage,
    ) -> ChatMessage:
        """
        Persist a new chat message.
        """

        return self._persist(message)

    def list_by_chat(
        self,
        chat_id: UUID,
    ) -> list[ChatMessage]:
        """
        Retrieve messages belonging to a chat.
        """

        stmt = (
            select(self.model)
            .where(
                self.model.chat_id == chat_id,
            )
            .order_by(
                self.model.created_at.asc(),
            )
        )

        return self._scalars(stmt).all()

    def list_recent(
        self,
        chat_id: UUID,
        limit: int = 20,
    ) -> list[ChatMessage]:
        """
        Retrieve the most recent messages in chronological order.
        """

        stmt = (
            select(self.model)
            .where(
                self.model.chat_id == chat_id,
            )
            .order_by(
                self.model.created_at.desc(),
            )
            .limit(limit)
        )

        messages = self._scalars(stmt).all()

        return list(reversed(messages))
