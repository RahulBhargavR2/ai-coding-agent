from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.core.exceptions import (
    ProjectAlreadyExists,
    WorkspaceNotFound,
)
from app.models.project import Project
from app.models.workspace import Workspace
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.workspace.project_service import ProjectService


@pytest.fixture
def project_uow():
    uow = Mock()

    uow.projects = Mock()
    uow.workspaces = Mock()

    return uow


@pytest.fixture
def project_service(project_uow):
    return ProjectService(project_uow)


def test_create_project_success(
    project_service,
    project_uow,
):
    user_id = uuid4()
    workspace_id = uuid4()

    workspace = Workspace(
        user_id=user_id,
        name="Workspace",
    )

    workspace.id = workspace_id

    request = ProjectCreate(
        name="Test Project",
        description="Test description",
    )

    project = Project(
        workspace_id=workspace_id,
        name="Test Project",
        description="Test description",
    )

    project_uow.workspaces.get_by_id_and_user.return_value = workspace
    project_uow.projects.exists_by_name_and_workspace.return_value = False
    project_uow.projects.create.return_value = project

    result = project_service.create_project(
        user_id=user_id,
        workspace_id=workspace_id,
        data=request,
    )

    project_uow.workspaces.get_by_id_and_user.assert_called_once_with(
        workspace_id,
        user_id,
    )

    project_uow.projects.exists_by_name_and_workspace.assert_called_once_with(
        workspace_id,
        "Test Project",
    )

    project_uow.projects.create.assert_called_once()
    project_uow.commit.assert_called_once()
    project_uow.refresh.assert_called_once_with(project)

    assert result is project


def test_create_project_raises_when_workspace_not_found(
    project_service,
    project_uow,
):
    project_uow.workspaces.get_by_id_and_user.return_value = None

    with pytest.raises(WorkspaceNotFound):
        project_service.create_project(
            user_id=uuid4(),
            workspace_id=uuid4(),
            data=ProjectCreate(
                name="Test Project",
            ),
        )

    project_uow.projects.create.assert_not_called()
    project_uow.commit.assert_not_called()


def test_create_project_raises_for_duplicate_name(
    project_service,
    project_uow,
):
    workspace = Workspace(
        user_id=uuid4(),
        name="Workspace",
    )

    project_uow.workspaces.get_by_id_and_user.return_value = workspace
    project_uow.projects.exists_by_name_and_workspace.return_value = True

    with pytest.raises(ProjectAlreadyExists):
        project_service.create_project(
            user_id=workspace.user_id,
            workspace_id=workspace.id,
            data=ProjectCreate(
                name="Existing Project",
            ),
        )

    project_uow.projects.create.assert_not_called()
    project_uow.commit.assert_not_called()


def test_get_project_success(
    project_service,
    project_uow,
):
    project = Project(
        workspace_id=uuid4(),
        name="Test Project",
    )

    project_uow.projects.get_by_id_and_user.return_value = project

    result = project_service.get_project(
        project_id=project.id,
        user_id=uuid4(),
    )

    assert result is project


def test_list_projects_success(
    project_service,
    project_uow,
):
    user_id = uuid4()
    workspace = Workspace(
        user_id=user_id,
        name="Workspace",
    )

    projects = [
        Project(
            workspace_id=workspace.id,
            name="Project One",
        ),
        Project(
            workspace_id=workspace.id,
            name="Project Two",
        ),
    ]

    project_uow.workspaces.get_by_id_and_user.return_value = workspace
    project_uow.projects.list_by_workspace.return_value = projects

    result = project_service.list_projects(
        workspace_id=workspace.id,
        user_id=user_id,
    )

    project_uow.projects.list_by_workspace.assert_called_once_with(
        workspace.id,
    )

    assert result == projects


def test_list_projects_raises_when_workspace_not_found(
    project_service,
    project_uow,
):
    project_uow.workspaces.get_by_id_and_user.return_value = None

    with pytest.raises(WorkspaceNotFound):
        project_service.list_projects(
            workspace_id=uuid4(),
            user_id=uuid4(),
        )

    project_uow.projects.list_by_workspace.assert_not_called()


def test_update_project_name(
    project_service,
    project_uow,
):
    project = Project(
        workspace_id=uuid4(),
        name="Old Name",
        description="Old description",
    )

    project_uow.projects.get_by_id_and_user.return_value = project
    project_uow.projects.exists_by_name_and_workspace.return_value = False

    result = project_service.update_project(
        project_id=project.id,
        user_id=uuid4(),
        data=ProjectUpdate(
            name="New Name",
        ),
    )

    assert result.name == "New Name"
    project_uow.commit.assert_called_once()
    project_uow.refresh.assert_called_once_with(project)


def test_update_project_description(
    project_service,
    project_uow,
):
    project = Project(
        workspace_id=uuid4(),
        name="Project",
        description="Old",
    )

    project_uow.projects.get_by_id_and_user.return_value = project

    result = project_service.update_project(
        project_id=project.id,
        user_id=uuid4(),
        data=ProjectUpdate(
            description="New",
        ),
    )

    assert result.description == "New"
    project_uow.commit.assert_called_once()


def test_update_project_duplicate_name(
    project_service,
    project_uow,
):
    project = Project(
        workspace_id=uuid4(),
        name="Old Name",
    )

    project_uow.projects.get_by_id_and_user.return_value = project
    project_uow.projects.exists_by_name_and_workspace.return_value = True

    with pytest.raises(ProjectAlreadyExists):
        project_service.update_project(
            project_id=project.id,
            user_id=uuid4(),
            data=ProjectUpdate(
                name="Existing Name",
            ),
        )

    project_uow.commit.assert_not_called()


def test_delete_project(
    project_service,
    project_uow,
):
    project = Project(
        workspace_id=uuid4(),
        name="Project",
    )

    project_uow.projects.get_by_id_and_user.return_value = project

    project_service.delete_project(
        project_id=project.id,
        user_id=uuid4(),
    )

    project_uow.projects.delete.assert_called_once_with(project)
    project_uow.commit.assert_called_once()
