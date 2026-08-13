
from fastapi import APIRouter, status
from uuid import UUID
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceListResponse,
    WorkspaceUpdate,
)

from app.dependencies.uow import UnitOfWorkDep
from app.dependencies.auth import CurrentActiveUser

from app.services.workspace.workspace_service import WorkspaceService

router = APIRouter(
    prefix="/workspaces",
    tags=["Workspaces"],
)


@router.post(
    "",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_workspace(
    request: WorkspaceCreate,
    current_user: CurrentActiveUser,
    uow: UnitOfWorkDep,
) -> WorkspaceResponse:

    service = WorkspaceService(uow)

    workspace = service.create(
        user_id=current_user.id,
        request=request,
    )

    return WorkspaceResponse.model_validate(workspace)


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
)
def get_workspace(
    workspace_id: UUID,
    current_user: CurrentActiveUser,
    uow: UnitOfWorkDep,
) -> WorkspaceResponse:

    service = WorkspaceService(uow)

    workspace = service.get(
        workspace_id=workspace_id,
        user_id=current_user.id,
    )

    return WorkspaceResponse.model_validate(workspace)


@router.get(
    "",
    response_model=WorkspaceListResponse,
)
def list_workspaces(
    current_user: CurrentActiveUser,
    uow: UnitOfWorkDep,
) -> WorkspaceListResponse:

    service = WorkspaceService(uow)

    workspaces = service.list(current_user.id)

    return WorkspaceListResponse(
        items=[WorkspaceResponse.model_validate(workspace) for workspace in workspaces],
        total=len(workspaces),
    )


@router.patch(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
)
def update_workspace(
    workspace_id: UUID,
    request: WorkspaceUpdate,
    current_user: CurrentActiveUser,
    uow: UnitOfWorkDep,
) -> WorkspaceResponse:

    service = WorkspaceService(uow)

    workspace = service.update(
        workspace_id=workspace_id,
        user_id=current_user.id,
        request=request,
    )

    return WorkspaceResponse.model_validate(workspace)


@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_workspace(
    workspace_id: UUID,
    current_user: CurrentActiveUser,
    uow: UnitOfWorkDep,
) -> None:

    service = WorkspaceService(uow)

    service.delete(
        workspace_id=workspace_id,
        user_id=current_user.id,
    )
