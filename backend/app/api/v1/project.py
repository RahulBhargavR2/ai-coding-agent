from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status, Response

from app.models.user import User

from app.services.workspace.project_service import ProjectService
from app.dependencies.auth import CurrentActiveUser
from app.dependencies.uow import UnitOfWorkDep
from app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectListResponse,
    ProjectUpdate,
)

router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)


@router.post(
    "/workspace/{workspace_id}",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    workspace_id: UUID,
    request: ProjectCreate,
    current_user: CurrentActiveUser,
    uow: UnitOfWorkDep,
) -> ProjectResponse:

    service = ProjectService(uow)

    project = service.create_project(
        user_id=current_user.id,
        workspace_id=workspace_id,
        data=request
    )

    return ProjectResponse.model_validate(project)


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
)
def get_project(
    project_id: UUID,
    current_user:CurrentActiveUser,
    uow:UnitOfWorkDep
) -> ProjectResponse:

    service = ProjectService(uow)

    project = service.get_project(
        project_id=project_id,
        user_id=current_user.id
    )

    return ProjectResponse.model_validate(project)


@router.get(
    "/workspace/{workspace_id}",
    response_model=ProjectListResponse,
)
def list_projects(
    workspace_id: UUID,
    current_user: CurrentActiveUser,
    uow:UnitOfWorkDep
) -> list[ProjectResponse]:

    service = ProjectService(uow)
    projects = service.list_projects(
        workspace_id=workspace_id,
        user_id=current_user.id,
    )

    return ProjectListResponse(
        items=[
            ProjectResponse.model_validate(project)
            for project in projects
        ],
        total=len(projects)
    )


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
)
def update_project(
    project_id: UUID,
    request: ProjectUpdate,
    current_user: CurrentActiveUser,
    uow:UnitOfWorkDep
) -> ProjectResponse:

    service = ProjectService(uow)

    project = service.update_project(
        project_id=project_id,
        user_id=current_user.id,
        data=request,
    )

    return ProjectResponse.model_validate(project)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_project(
    project_id: UUID,
    current_user: CurrentActiveUser,
    uow:UnitOfWorkDep
):
    service = ProjectService(uow)
    service.delete_project(
        project_id=project_id,
        user_id=current_user.id,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
