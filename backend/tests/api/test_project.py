from uuid import uuid4

import pytest

from app.models.project import Project
from app.models.workspace import Workspace
from app.services.auth.jwt_service import JWTService

base_url = "/api/v1"
@pytest.fixture
def auth_headers(user):
    jwt_service = JWTService()

    token = jwt_service.create_access_token(
        subject=str(user.id),
    )

    return {
        "Authorization": f"Bearer {token}",
    }


@pytest.fixture
def workspace(db_session, user):
    workspace = Workspace(
        user_id=user.id,
        name="Test Workspace",
    )

    db_session.add(workspace)
    db_session.flush()

    return workspace


def test_create_project(
    client,
    user,
    workspace,
    auth_headers,
):
    response = client.post(
        base_url+f"/projects/workspace/{workspace.id}",
        json={
            "name": "Test Project",
            "description": "Project description",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Test Project"
    assert data["description"] == "Project description"
    assert data["workspace_id"] == str(workspace.id)


def test_create_project_without_authentication(
    client,
    workspace,
):
    response = client.post(
        base_url+f"/projects/workspace/{workspace.id}",
        json={
            "name": "Test Project",
        },
    )

    assert response.status_code == 401


def test_create_project_workspace_not_found(
    client,
    auth_headers,
):
    response = client.post(
        base_url+f"/projects/workspace/{uuid4()}",
        json={
            "name": "Test Project",
        },
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_create_duplicate_project(
    client,
    workspace,
    auth_headers,
    db_session,
):
    project = Project(
        workspace_id=workspace.id,
        name="Existing Project",
    )

    db_session.add(project)
    db_session.flush()

    response = client.post(
        base_url+f"/projects/workspace/{workspace.id}",
        json={
            "name": "Existing Project",
        },
        headers=auth_headers,
    )

    assert response.status_code == 409


def test_get_project(
    client,
    workspace,
    auth_headers,
    db_session,
):
    project = Project(
        workspace_id=workspace.id,
        name="Test Project",
    )

    db_session.add(project)
    db_session.flush()

    response = client.get(
        base_url+f"/projects/{project.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(project.id)
    assert data["name"] == "Test Project"


def test_get_project_not_found(
    client,
    auth_headers,
):
    response = client.get(
        base_url+f"/projects/{uuid4()}",
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_get_project_from_another_user(
    client,
    user,
    user_factory,
    db_session,
):
    workspace = Workspace(
        user_id=user.id,
        name="Private Workspace",
    )

    db_session.add(workspace)
    db_session.flush()

    project = Project(
        workspace_id=workspace.id,
        name="Private Project",
    )

    db_session.add(project)
    db_session.flush()

    another_user = user_factory()

    jwt_service = JWTService()

    token = jwt_service.create_access_token(
        subject=str(another_user.id),
    )

    response = client.get(
       base_url+ f"/projects/{project.id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 404


def test_list_projects(
    client,
    workspace,
    auth_headers,
    db_session,
):
    project_one = Project(
        workspace_id=workspace.id,
        name="Project One",
    )

    project_two = Project(
        workspace_id=workspace.id,
        name="Project Two",
    )

    db_session.add_all(
        [
            project_one,
            project_two,
        ]
    )
    db_session.flush()

    response = client.get(
        base_url+f"/projects/workspace/{workspace.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_list_projects_workspace_not_found(
    client,
    auth_headers,
):
    response = client.get(
        base_url + f"/projects/workspace/{uuid4()}",
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_update_project(
    client,
    workspace,
    auth_headers,
    db_session,
):
    project = Project(
        workspace_id=workspace.id,
        name="Old Project",
        description="Old description",
    )

    db_session.add(project)
    db_session.flush()

    response = client.patch(
        base_url + f"/projects/{project.id}",
        json={
            "name": "New Project",
            "description": "New description",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "New Project"
    assert data["description"] == "New description"


def test_update_project_duplicate_name(
    client,
    workspace,
    auth_headers,
    db_session,
):
    project_one = Project(
        workspace_id=workspace.id,
        name="Project One",
    )

    project_two = Project(
        workspace_id=workspace.id,
        name="Project Two",
    )

    db_session.add_all(
        [
            project_one,
            project_two,
        ]
    )
    db_session.flush()

    response = client.patch(
        base_url + f"/projects/{project_two.id}",
        json={
            "name": "Project One",
        },
        headers=auth_headers,
    )

    assert response.status_code == 409


def test_delete_project(
    client,
    workspace,
    auth_headers,
    db_session,
):
    project = Project(
        workspace_id=workspace.id,
        name="Project To Delete",
    )

    db_session.add(project)
    db_session.flush()

    response = client.delete(
        base_url + f"/projects/{project.id}",
        headers=auth_headers,
    )

    assert response.status_code == 204
    assert response.content == b""

    assert (
        db_session.get(
            Project,
            project.id,
        )
        is None
    )


def test_delete_project_not_found(
    client,
    auth_headers,
):
    response = client.delete(
        base_url + f"/projects/{uuid4()}",
        headers=auth_headers,
    )

    assert response.status_code == 404
