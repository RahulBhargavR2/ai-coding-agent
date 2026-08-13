from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.core.exceptions import (
    WorkspaceAlreadyExists,
    WorkspaceNotFound,
)
from app.models.workspace import Workspace
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate
from app.services.workspace.workspace_service import WorkspaceService


@pytest.fixture
def workspace_uow():
    uow = Mock()

    uow.workspaces = Mock()

    return uow


@pytest.fixture
def workspace_service(workspace_uow):
    return WorkspaceService(workspace_uow)


def test_create_workspace_success(
    workspace_service,
    workspace_uow,
):
    user_id = uuid4()

    request = WorkspaceCreate(
        name="Test Workspace",
        description="Test description",
    )

    workspace = Workspace(
        user_id=user_id,
        name=request.name,
        description=request.description,
    )

    workspace_uow.workspaces.exists_by_name_and_user.return_value = False
    workspace_uow.workspaces.create.return_value = workspace

    result = workspace_service.create(
        user_id=user_id,
        request=request,
    )

    workspace_uow.workspaces.exists_by_name_and_user.assert_called_once_with(
        user_id=user_id,
        name="Test Workspace",
    )

    workspace_uow.workspaces.create.assert_called_once()

    workspace_uow.commit.assert_called_once()

    assert result is workspace


def test_create_workspace_raises_when_name_exists(
    workspace_service,
    workspace_uow,
):
    user_id = uuid4()

    request = WorkspaceCreate(
        name="Existing Workspace",
        description="Test description",
    )

    workspace_uow.workspaces.exists_by_name_and_user.return_value = True

    with pytest.raises(WorkspaceAlreadyExists):
        workspace_service.create(
            user_id=user_id,
            request=request,
        )

    workspace_uow.workspaces.create.assert_not_called()
    workspace_uow.commit.assert_not_called()


def test_get_workspace_success(
    workspace_service,
    workspace_uow,
):
    workspace_id = uuid4()
    user_id = uuid4()

    workspace = Workspace(
        user_id=user_id,
        name="Test Workspace",
    )

    workspace.id = workspace_id

    workspace_uow.workspaces.get_by_id_and_user.return_value = workspace

    result = workspace_service.get(
        workspace_id=workspace_id,
        user_id=user_id,
    )

    workspace_uow.workspaces.get_by_id_and_user.assert_called_once_with(
        workspace_id=workspace_id,
        user_id=user_id,
    )

    assert result is workspace


def test_get_workspace_raises_when_not_found(
    workspace_service,
    workspace_uow,
):
    workspace_uow.workspaces.get_by_id_and_user.return_value = None

    workspace_id = uuid4()
    user_id = uuid4()

    with pytest.raises(WorkspaceNotFound):
        workspace_service.get(
            workspace_id=workspace_id,
            user_id=user_id,
        )


def test_list_workspaces(
    workspace_service,
    workspace_uow,
):
    user_id = uuid4()

    workspaces = [
        Workspace(
            user_id=user_id,
            name="Workspace One",
        ),
        Workspace(
            user_id=user_id,
            name="Workspace Two",
        ),
    ]

    workspace_uow.workspaces.list_by_user.return_value = workspaces

    result = workspace_service.list(user_id)

    workspace_uow.workspaces.list_by_user.assert_called_once_with(
        user_id,
    )

    assert result == workspaces


def test_update_workspace_name(
    workspace_service,
    workspace_uow,
):
    user_id = uuid4()

    workspace = Workspace(
        user_id=user_id,
        name="Old Name",
        description="Old description",
    )

    workspace_uow.workspaces.get_by_id_and_user.return_value = workspace
    workspace_uow.workspaces.exists_by_name_and_user.return_value = False

    request = WorkspaceUpdate(
        name="New Name",
    )

    result = workspace_service.update(
        workspace_id=workspace.id,
        user_id=user_id,
        request=request,
    )

    assert result.name == "New Name"

    workspace_uow.commit_and_refresh.assert_called_once_with(
        workspace,
    )


def test_update_workspace_description(
    workspace_service,
    workspace_uow,
):
    user_id = uuid4()

    workspace = Workspace(
        user_id=user_id,
        name="Workspace",
        description="Old description",
    )

    workspace_uow.workspaces.get_by_id_and_user.return_value = workspace

    request = WorkspaceUpdate(
        description="New description",
    )

    result = workspace_service.update(
        workspace_id=workspace.id,
        user_id=user_id,
        request=request,
    )

    assert result.description == "New description"

    workspace_uow.commit_and_refresh.assert_called_once_with(
        workspace,
    )


def test_update_workspace_raises_for_duplicate_name(
    workspace_service,
    workspace_uow,
):
    user_id = uuid4()

    workspace = Workspace(
        user_id=user_id,
        name="Old Name",
    )

    workspace_uow.workspaces.get_by_id_and_user.return_value = workspace
    workspace_uow.workspaces.exists_by_name_and_user.return_value = True

    request = WorkspaceUpdate(
        name="Existing Name",
    )

    with pytest.raises(WorkspaceAlreadyExists):
        workspace_service.update(
            workspace_id=workspace.id,
            user_id=user_id,
            request=request,
        )

    workspace_uow.commit_and_refresh.assert_not_called()


def test_update_workspace_not_found(
    workspace_service,
    workspace_uow,
):
    workspace_uow.workspaces.get_by_id_and_user.return_value = None

    with pytest.raises(WorkspaceNotFound):
        workspace_service.update(
            workspace_id=uuid4(),
            user_id=uuid4(),
            request=WorkspaceUpdate(name="New Name"),
        )


def test_delete_workspace(
    workspace_service,
    workspace_uow,
):
    workspace = Workspace(
        user_id=uuid4(),
        name="Workspace",
    )

    workspace_uow.workspaces.get_by_id_and_user.return_value = workspace

    workspace_service.delete(
        workspace_id=workspace.id,
        user_id=workspace.user_id,
    )

    workspace_uow.workspaces.delete.assert_called_once_with(
        workspace,
    )

    workspace_uow.commit.assert_called_once()


def test_delete_workspace_not_found(
    workspace_service,
    workspace_uow,
):
    workspace_uow.workspaces.get_by_id_and_user.return_value = None

    with pytest.raises(WorkspaceNotFound):
        workspace_service.delete(
            workspace_id=uuid4(),
            user_id=uuid4(),
        )

    workspace_uow.workspaces.delete.assert_not_called()
    workspace_uow.commit.assert_not_called()
