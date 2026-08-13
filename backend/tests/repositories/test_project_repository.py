from uuid import uuid4

from app.models.project import Project
from app.models.workspace import Workspace
from app.repositories.project_repository import ProjectRepository


def test_create_project(db_session, user):
    repository = ProjectRepository(db_session)

    workspace = Workspace(
        user_id=user.id,
        name="Test Workspace",
    )

    db_session.add(workspace)
    db_session.flush()

    project = Project(
        workspace_id=workspace.id,
        name="Test Project",
        description="Test description",
    )

    result = repository.create(project)

    db_session.flush()

    assert result.id is not None
    assert result.workspace_id == workspace.id
    assert result.name == "Test Project"


def test_get_by_id_and_user_returns_project(
    db_session,
    user,
):
    repository = ProjectRepository(db_session)

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

    result = repository.get_by_id_and_user(
        project_id=project.id,
        user_id=user.id,
    )

    assert result is not None
    assert result.id == project.id


def test_get_by_id_and_user_returns_none_for_wrong_user(
    db_session,
    user,
    user_factory,
):
    repository = ProjectRepository(db_session)

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

    another_user = user_factory()

    result = repository.get_by_id_and_user(
        project_id=project.id,
        user_id=another_user.id,
    )

    assert result is None


def test_get_by_id_and_user_returns_none_for_unknown_project(
    db_session,
    user,
):
    repository = ProjectRepository(db_session)

    result = repository.get_by_id_and_user(
        project_id=uuid4(),
        user_id=user.id,
    )

    assert result is None


def test_list_by_workspace(db_session, user):
    repository = ProjectRepository(db_session)

    workspace = Workspace(
        user_id=user.id,
        name="Test Workspace",
    )

    db_session.add(workspace)
    db_session.flush()

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

    result = repository.list_by_workspace(workspace.id)

    assert len(result) == 2
    assert {project.name for project in result} == {
        "Project One",
        "Project Two",
    }


def test_list_by_workspace_returns_empty_for_unknown_workspace(
    db_session,
):
    repository = ProjectRepository(db_session)

    result = repository.list_by_workspace(uuid4())

    assert result == []


def test_exists_by_name_and_workspace(
    db_session,
    user,
):
    repository = ProjectRepository(db_session)

    workspace = Workspace(
        user_id=user.id,
        name="Test Workspace",
    )

    db_session.add(workspace)
    db_session.flush()

    project = Project(
        workspace_id=workspace.id,
        name="My Project",
    )

    db_session.add(project)
    db_session.flush()

    assert repository.exists_by_name_and_workspace(
        workspace_id=workspace.id,
        name="My Project",
    )


def test_exists_by_name_and_workspace_is_case_insensitive(
    db_session,
    user,
):
    repository = ProjectRepository(db_session)

    workspace = Workspace(
        user_id=user.id,
        name="Test Workspace",
    )

    db_session.add(workspace)
    db_session.flush()

    project = Project(
        workspace_id=workspace.id,
        name="My Project",
    )

    db_session.add(project)
    db_session.flush()

    assert repository.exists_by_name_and_workspace(
        workspace_id=workspace.id,
        name="my project",
    )


def test_exists_by_name_and_workspace_returns_false(
    db_session,
    user,
):
    repository = ProjectRepository(db_session)

    workspace = Workspace(
        user_id=user.id,
        name="Test Workspace",
    )

    db_session.add(workspace)
    db_session.flush()

    assert not repository.exists_by_name_and_workspace(
        workspace_id=workspace.id,
        name="Unknown Project",
    )


def test_delete_project(db_session, user):
    repository = ProjectRepository(db_session)

    workspace = Workspace(
        user_id=user.id,
        name="Test Workspace",
    )

    db_session.add(workspace)
    db_session.flush()

    project = Project(
        workspace_id=workspace.id,
        name="Project To Delete",
    )

    db_session.add(project)
    db_session.flush()

    repository.delete(project)

    db_session.flush()

    result = repository.get_by_id_and_user(
        project.id,
        user.id,
    )

    assert result is None
