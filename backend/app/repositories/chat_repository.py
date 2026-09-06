from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chat import Chat
from app.models.project import Project
from app.models.repository import Repository
from app.models.workspace import Workspace
from app.repositories.base_repository import BaseRepository


class ChatRepository(BaseRepository[Chat]):
    """
    Handles persistence operations for chats.
    """

    def __init__(self, db: Session) -> None:
        super().__init__(db, Chat)

    def create(
        self,
        chat: Chat,
    ) -> Chat:
        """
        Persist a new chat.
        """

        return self._persist(chat)

    def get_by_id(
        self,
        chat_id: UUID,
    ) -> Chat | None:
        """
        Retrieve a chat by ID.
        """

        stmt = select(self.model).where(
            self.model.id == chat_id,
        )

        return self._first(stmt)

    def get_by_id_and_user(
        self,
        chat_id: UUID,
        user_id: UUID,
    ) -> Chat | None:
        """
        Retrieve a chat only if it belongs to the given user.
        """

        stmt = (
            select(self.model)
            .join(Repository)
            .join(Project)
            .join(Workspace)
            .where(
                self.model.id == chat_id,
                Workspace.user_id == user_id,
            )
        )

        return self._first(stmt)

    def list_by_repository(
        self,
        repository_id: UUID,
        user_id: UUID,
    ) -> list[Chat]:
        """
        Retrieve chats for a repository owned by the user.
        """

        stmt = (
            select(self.model)
            .join(Repository)
            .join(Project)
            .join(Workspace)
            .where(
                self.model.repository_id == repository_id,
                Workspace.user_id == user_id,
            )
            .order_by(
                self.model.updated_at.desc(),
            )
        )

        return self._scalars(stmt).all()
