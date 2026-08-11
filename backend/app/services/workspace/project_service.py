from __future__ import annotations

from uuid import UUID

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.dependencies.uow import UnitOfWorkDep
from app.core.exceptions import WorkspaceNotFound, ProjectAlreadyExists


class ProjectService:

    def __init__(
        self,
        uow: UnitOfWorkDep,
    ) -> None:
        self.uow = uow

    def create_project(
        self,
        user_id: UUID,
        workspace_id: UUID,
        data: ProjectCreate,
    ) -> Project:

        workspace = self.uow.workspaces.get_by_id_and_user(
            workspace_id,
            user_id,
        )

        if workspace is None:
            raise WorkspaceNotFound("Workspace not found.")

        if self.uow.projects.exists_by_name_and_workspace(
            workspace_id,
            data.name,
        ):
            raise ProjectAlreadyExists("Project already exists.")

        project = Project(
            workspace_id=workspace.id,
            name=data.name,
            description=data.description,
        )

        project = self.uow.projects.create(project)

        self.uow.commit()
        self.uow.refresh(project)

        return project

    def get_project(
        self,
        project_id: UUID,
        user_id: UUID,
    ) -> Project:

        project = self.uow.projects.get_by_id_and_user(
            project_id,
            user_id,
        )

        if project is None:
            raise ValueError("Project not found.")

        return project

    def list_projects(
        self,
        workspace_id: UUID,
        user_id: UUID,
    ) -> list[Project]:

        workspace = self.uow.workspaces.get_by_id_and_user(
            workspace_id,
            user_id,
        )

        if workspace is None:
            raise WorkspaceNotFound("Workspace not found.")

        return self.uow.projects.list_by_workspace(
            workspace_id,
        )

    def update_project(
        self,
        project_id: UUID,
        user_id: UUID,
        data: ProjectUpdate,
    ) -> Project:

        project = self.get_project(
            project_id,
            user_id,
        )

        if (
            data.name is not None
            and data.name != project.name
            and self.uow.projects.exists_by_name_and_workspace(
                project.workspace_id,
                data.name,
            )
        ):
            raise ProjectAlreadyExists("Project with this name already exists.")

        update_data = data.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        for field, value in update_data.items():
            setattr(project, field, value)

        self.uow.commit()
        self.uow.refresh(project)

        return project

    def delete_project(
        self,
        project_id: UUID,
        user_id: UUID,
    ) -> None:

        project = self.get_project(
            project_id,
            user_id,
        )

        self.uow.projects.delete(project)

        self.uow.commit()
