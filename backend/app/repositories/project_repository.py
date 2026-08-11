from __future__ import annotations

from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.workspace import Workspace
from app.repositories.base_repository import BaseRepository


class ProjectRepository(BaseRepository[Project]):

    def __init__(self, db: Session) -> None:
        super().__init__(db, Project)

    def create(self, project: Project) -> Project:
        """
        Persist a new Project
        """
        return self._persist(project)

    def get_by_id_and_user(self, project_id: UUID, user_id: UUID) -> Project | None:

        stmt = (
            select(self.model)
            .join(Workspace)
            .where(
                self.model.id == project_id,
                Workspace.user_id == user_id,
            )
        )

        return self._first(stmt)

    def list_by_workspace(self, workspace_id: UUID) -> list[Project]:

        stmt = (
            select(self.model)
            .join(Workspace)
            .where(
                self.model.workspace_id == workspace_id,
            )
            .order_by(self.model.updated_at.desc())
        )

        return list(self._scalars(stmt).all())

    def exists_by_name_and_workspace(
        self,
        workspace_id: UUID,
        name: str
    ) -> bool:
        stmt = (
            select(self.model.id)
            .where(
                self.model.workspace_id == workspace_id,
                func.lower(self.model.name) == name.lower(),
            )
            .limit(1)
        )

        return self._scalar(stmt) is not None

    def delete(
        self,
        project: Project
    ) -> None:

        super().delete(project)
