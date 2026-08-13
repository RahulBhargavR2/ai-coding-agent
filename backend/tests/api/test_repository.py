from uuid import uuid4

import pytest

from app.models.enums import RepositoryProvider, RepositoryStatus
from app.models.project import Project
from app.models.repository import Repository
from app.models.workspace import Workspace
from app.services.auth.jwt_service import JWTService

base_url ="/api/v1"
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
def project(db_session, user):
    workspace = Workspace(
        user_id=user.id,
        name="Test Workspace",
    )

    db_session.add(workspace)
    db_session.flush()

    project = Project(
        workspace_id=workspace.id,
        name="Test Project",
    )

    db_session.add(project)
    db_session.flush()

    return project


def create_repository(
    db_session,
    project,
    *,
    name="test-repository",
    url="https://github.com/test/test-repository.git",
):
    repository = Repository(
        project_id=project.id,
        name=name,
        provider=RepositoryProvider.GITHUB,
        url=url,
        default_branch="main",
        current_branch="main",
        status=RepositoryStatus.PENDING,
    )

    db_session.add(repository)
    db_session.flush()

    return repository


# ============================================================================
# GitHub Import
# ============================================================================


def test_import_github_repository(
    client,
    project,
    auth_headers,
):
    response = client.post(
        base_url+"/repositories/import/github",
        json={
            "project_id": str(project.id),
            "url": "https://github.com/openai/test-repository.git",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["project_id"] == str(project.id)
    assert data["name"] == "test-repository"
    assert data["provider"] == "github"
    assert data["status"] == "pending"


def test_import_github_repository_without_authentication(
    client,
    project,
):
    response = client.post(
        base_url+"/repositories/import/github",
        json={
            "project_id": str(project.id),
            "url": "https://github.com/openai/test-repository.git",
        },
    )

    assert response.status_code == 401


def test_import_github_repository_project_not_found(
    client,
    auth_headers,
):
    response = client.post(
        base_url+"/repositories/import/github",
        json={
            "project_id": str(uuid4()),
            "url": "https://github.com/openai/test-repository.git",
        },
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_import_duplicate_github_repository(
    client,
    project,
    auth_headers,
    db_session,
):
    url = "https://github.com/openai/existing-repository.git"

    create_repository(
        db_session,
        project,
        name="existing-repository",
        url=url,
    )

    response = client.post(
        base_url+"/repositories/import/github",
        json={
            "project_id": str(project.id),
            "url": url,
        },
        headers=auth_headers,
    )

    assert response.status_code == 409


# ============================================================================
# Upload
# ============================================================================


def test_upload_repository(
    client,
    project,
    auth_headers,
):
    response = client.post(
        base_url+"/repositories/import/upload",
        data={
            "project_id": str(project.id),
            "name": "uploaded-repository",
        },
        files={
            "file": (
                "repository.zip",
                b"fake zip content",
                "application/zip",
            )
        },
        headers=auth_headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["project_id"] == str(project.id)
    assert data["name"] == "uploaded-repository"
    assert data["provider"] == "upload"
    assert data["status"] == "pending"


def test_upload_repository_without_authentication(
    client,
    project,
):
    response = client.post(
        base_url+"/repositories/import/upload",
        data={
            "project_id": str(project.id),
            "name": "uploaded-repository",
        },
        files={
            "file": (
                "repository.zip",
                b"fake zip content",
                "application/zip",
            )
        },
    )

    assert response.status_code == 401


def test_upload_repository_project_not_found(
    client,
    auth_headers,
):
    response = client.post(
        base_url+"/repositories/import/upload",
        data={
            "project_id": str(uuid4()),
            "name": "uploaded-repository",
        },
        files={
            "file": (
                "repository.zip",
                b"fake zip content",
                "application/zip",
            )
        },
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_upload_duplicate_repository(
    client,
    project,
    auth_headers,
    db_session,
):
    create_repository(
        db_session,
        project,
        name="existing-repository",
        url="https://github.com/test/existing.git",
    )

    response = client.post(
        base_url+"/repositories/import/upload",
        data={
            "project_id": str(project.id),
            "name": "existing-repository",
        },
        files={
            "file": (
                "repository.zip",
                b"fake zip content",
                "application/zip",
            )
        },
        headers=auth_headers,
    )

    assert response.status_code == 409


# ============================================================================
# Get
# ============================================================================


def test_get_repository(
    client,
    project,
    auth_headers,
    db_session,
):
    repository = create_repository(
        db_session,
        project,
    )

    response = client.get(
        base_url+f"/repositories/{repository.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(repository.id)
    assert data["name"] == "test-repository"


def test_get_repository_not_found(
    client,
    auth_headers,
):
    response = client.get(
        base_url+f"/repositories/{uuid4()}",
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_get_repository_from_another_user(
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

    repository = create_repository(
        db_session,
        project,
    )

    another_user = user_factory()

    jwt_service = JWTService()

    token = jwt_service.create_access_token(
        subject=str(another_user.id),
    )

    response = client.get(
        base_url+f"/repositories/{repository.id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 404


# ============================================================================
# List
# ============================================================================


def test_list_project_repositories(
    client,
    project,
    auth_headers,
    db_session,
):
    create_repository(
        db_session,
        project,
        name="repo-one",
        url="https://github.com/test/repo-one.git",
    )

    create_repository(
        db_session,
        project,
        name="repo-two",
        url="https://github.com/test/repo-two.git",
    )

    response = client.get(
        base_url+f"/repositories/project/{project.id}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2


def test_list_project_repositories_project_not_found(
    client,
    auth_headers,
):
    response = client.get(
        base_url+f"/repositories/project/{uuid4()}",
        headers=auth_headers,
    )

    assert response.status_code == 404


# ============================================================================
# Delete
# ============================================================================


def test_delete_repository(
    client,
    project,
    auth_headers,
    db_session,
):
    repository = create_repository(
        db_session,
        project,
    )

    response = client.delete(
        base_url+f"/repositories/{repository.id}",
        headers=auth_headers,
    )

    assert response.status_code == 204
    assert response.content == b""

    assert (
        db_session.get(
            Repository,
            repository.id,
        )
        is None
    )


def test_delete_repository_not_found(
    client,
    auth_headers,
):
    response = client.delete(
        base_url+f"/repositories/{uuid4()}",
        headers=auth_headers,
    )

    assert response.status_code == 404
