from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.workspace import Workspace
from app.repositories.base_repository import BaseRepository


class WorkspaceRepository(BaseRepository[Workspace]):
    """
    Repository for Workspace persistence.

    All queries are ownership-aware.
    """

    def __init__(self, db: Session) -> None:
        super().__init__(db, Workspace)

    def create(
        self,
        workspace: Workspace,
    ) -> Workspace:
        """
        Persist a new workspace.
        """
        
        return self._persist(workspace)

    def get_by_id_and_user(
        self,
        workspace_id: UUID,
        user_id: UUID,
    ) -> Workspace | None:
        """
        Retrieve a workspace owned by a specific user.
        """
        stmt = select(self.model).where(
            self.model.id == workspace_id,
            self.model.user_id == user_id,
        )

        return self._first(stmt)

    def list_by_user(
        self,
        user_id: UUID,
    ) -> list[Workspace]:
        """
        List all workspaces belonging to a user.
        """
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(self.model.updated_at.desc())
        )

        return list(self._scalars(stmt).all())

    def exists_by_name_and_user(
        self,
        user_id: UUID,
        name: str,
    ) -> bool:
        """
        Check whether a workspace with the given name already exists
        for the specified user.
        """
        stmt = (
            select(self.model.id)
            .where(
                self.model.user_id == user_id,
                self.model.name == name,
            )
            .limit(1)
        )

        return self._scalar(stmt) is not None

    def delete(
        self,
        workspace: Workspace,
    ) -> None:
        """
        Delete an existing workspace.
        """
        super().delete(workspace)
