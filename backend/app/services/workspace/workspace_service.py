from __future__ import annotations

from uuid import UUID

from app.core.unit_of_work import UnitOfWork

from app.core.exceptions import (
    WorkspaceNotFound,
    WorkspaceAlreadyExists
)

from app.models.workspace import Workspace
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceUpdate,
)


class WorkspaceService:
    """Business logic for workspace management."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def create(
        self,
        user_id: UUID,
        request: WorkspaceCreate,
    ) -> Workspace:
        """
        Create a new workspace.
        """

        if self.uow.workspaces.exists_by_name_and_user(
            user_id=user_id,
            name=request.name,
        ):
            raise WorkspaceAlreadyExists(request.name)

        workspace = Workspace(
            user_id=user_id,
            name=request.name,
            description=request.description,
        )

        workspace = self.uow.workspaces.create(workspace)

        self.uow.commit()

        return workspace

    def get(
        self,
        workspace_id: UUID,
        user_id: UUID,
    ) -> Workspace:
        """
        Retrieve a workspace owned by a user.
        """
        return self._get_workspace(
            workspace_id=workspace_id,
            user_id=user_id,
        )

    def list(
        self,
        user_id: UUID,
    ) -> list[Workspace]:
        """
        List all workspaces for a user.
        """
        return self.uow.workspaces.list_by_user(user_id)

    def update(
        self,
        workspace_id: UUID,
        user_id: UUID,
        request: WorkspaceUpdate,
    ) -> Workspace:
        """
        Update an existing workspace.
        """
        workspace = self._get_workspace(
            workspace_id,
            user_id,
        )

        if request.name is not None and request.name != workspace.name:
            if self.uow.workspaces.exists_by_name_and_user(
                user_id=user_id,
                name=request.name,
            ):
                raise WorkspaceAlreadyExists(request.name)

            workspace.name = request.name

        if request.description is not None:
            workspace.description = request.description

        self.uow.commit_and_refresh(workspace)

        return workspace

    def delete(
        self,
        workspace_id: UUID,
        user_id: UUID,
    ) -> None:
        """
        Delete a workspace.
        """
        workspace = self._get_workspace(
            workspace_id,
            user_id,
        )

        self.uow.workspaces.delete(workspace)

        self.uow.commit()

    def _get_workspace(
        self,
        workspace_id: UUID,
        user_id: UUID,
    ) -> Workspace:
        """
        Retrieve a workspace or raise an exception.
        """
        workspace = self.uow.workspaces.get_by_id_and_user(
            workspace_id=workspace_id,
            user_id=user_id,
        )

        if workspace is None:
            raise WorkspaceNotFound(str(workspace_id))

        return workspace
