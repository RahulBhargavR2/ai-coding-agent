from uuid import uuid4

import pytest

from app.models.workspace import Workspace
from app.services.auth.jwt_service import JWTService

base_url="/api/v1"
@pytest.fixture
def auth_headers(user):
    jwt_service = JWTService()

    token = jwt_service.create_access_token(
        subject=str(user.id),
    )

    return {
        "Authorization": f"Bearer {token}",
    }


def test_create_workspace(client, user, auth_headers):
    response = client.post(
        base_url+"/workspaces",
        json={
            "name": "Test Workspace",
            "description": "Test workspace description",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201

    data = response.json()


    assert data["name"] == "Test Workspace"
    assert data["description"] == "Test workspace description"
    assert data["user_id"] == str(user.id)


def test_create_workspace_without_authentication(client):
    response = client.post(
        base_url+"/workspaces",
        json={
            "name": "Test Workspace",
            "description": "Test description",
        },
    )

    assert response.status_code == 401


def test_create_duplicate_workspace(
    client,
    user,
    auth_headers,
    db_session,
):
    workspace = Workspace(
        user_id=user.id,
        name="Existing Workspace",
        description="Existing description",
    )

    db_session.add(workspace)
    db_session.flush()

    response = client.post(
        base_url+"/workspaces",
        json={
            "name": "Existing Workspace",
            "description": "Another description",
        },
        headers=auth_headers,
    )

    assert response.status_code == 409


def test_get_workspace(
    client,
    user,
    auth_headers,
    db_session,
):
    workspace = Workspace(
        user_id=user.id,
        name="Test Workspace",
        description="Description",
    )

    db_session.add(workspace)
    db_session.flush()

    response = client.get(
        base_url+ f"/workspaces/{workspace.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(workspace.id)
    assert data["name"] == "Test Workspace"


def test_get_workspace_not_found(
    client,
    auth_headers,
):
    response = client.get(
        base_url+ f"/workspaces/{uuid4()}",
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_get_workspace_from_another_user(
    client,
    user,
    user_factory,
    auth_headers,
    db_session,
):
    workspace = Workspace(
        user_id=user.id,
        name="Private Workspace",
    )

    db_session.add(workspace)
    db_session.flush()

    another_user = user_factory()

    jwt_service = JWTService()

    token = jwt_service.create_access_token(
        subject=str(another_user.id),
    )

    headers = {
        "Authorization": f"Bearer {token}",
    }

    response = client.get(
        base_url+ f"/workspaces/{workspace.id}",
        headers=headers,
    )

    assert response.status_code == 404


def test_list_workspaces(
    client,
    user,
    auth_headers,
    db_session,
):
    workspace_one = Workspace(
        user_id=user.id,
        name="Workspace One",
    )

    workspace_two = Workspace(
        user_id=user.id,
        name="Workspace Two",
    )

    db_session.add_all(
        [
            workspace_one,
            workspace_two,
        ]
    )
    db_session.flush()

    response = client.get(
        base_url+"/workspaces",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_list_workspaces_does_not_return_other_users(
    client,
    user,
    user_factory,
    auth_headers,
    db_session,
):
    another_user = user_factory()

    db_session.add_all(
        [
            Workspace(
                user_id=user.id,
                name="My Workspace",
            ),
            Workspace(
                user_id=another_user.id,
                name="Other Workspace",
            ),
        ]
    )

    db_session.flush()

    response = client.get(
        base_url+"/workspaces",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["name"] == "My Workspace"


def test_update_workspace(
    client,
    user,
    auth_headers,
    db_session,
):
    workspace = Workspace(
        user_id=user.id,
        name="Old Name",
        description="Old description",
    )

    db_session.add(workspace)
    db_session.flush()

    response = client.patch(
        base_url+f"/workspaces/{workspace.id}",
        json={
            "name": "New Name",
            "description": "New description",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "New Name"
    assert data["description"] == "New description"


def test_update_workspace_duplicate_name(
    client,
    user,
    auth_headers,
    db_session,
):
    workspace_one = Workspace(
        user_id=user.id,
        name="Workspace One",
    )

    workspace_two = Workspace(
        user_id=user.id,
        name="Workspace Two",
    )

    db_session.add_all(
        [
            workspace_one,
            workspace_two,
        ]
    )
    db_session.flush()

    response = client.patch(
        base_url+f"/workspaces/{workspace_two.id}",
        json={
            "name": "Workspace One",
        },
        headers=auth_headers,
    )

    assert response.status_code == 409


def test_delete_workspace(
    client,
    user,
    auth_headers,
    db_session,
):
    workspace = Workspace(
        user_id=user.id,
        name="Workspace To Delete",
    )

    db_session.add(workspace)
    db_session.flush()

    response = client.delete(
        base_url+f"/workspaces/{workspace.id}",
        headers=auth_headers,
    )

    assert response.status_code == 204
    assert response.content == b""

    assert (
        db_session.get(
            Workspace,
            workspace.id,
        )
        is None
    )


def test_delete_workspace_not_found(
    client,
    auth_headers,
):
    response = client.delete(
        base_url+f"/workspaces/{uuid4()}",
        headers=auth_headers,
    )

    assert response.status_code == 404
