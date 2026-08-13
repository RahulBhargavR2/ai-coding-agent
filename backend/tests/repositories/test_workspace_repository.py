from uuid import uuid4

from app.models.workspace import Workspace
from app.repositories.workspace_repository import WorkspaceRepository


def test_create_workspace(db_session, user):
    repository = WorkspaceRepository(db_session)

    workspace = Workspace(
        user_id=user.id,
        name="Test Workspace",
        description="Test description",
    )

    result = repository.create(workspace)

    db_session.flush()

    assert result.id is not None
    assert result.user_id == user.id
    assert result.name == "Test Workspace"


def test_get_by_id_and_user_returns_workspace(db_session, user):
    repository = WorkspaceRepository(db_session)

    workspace = Workspace(
        user_id=user.id,
        name="Test Workspace",
        description="Test description",
    )

    db_session.add(workspace)
    db_session.flush()

    result = repository.get_by_id_and_user(
        workspace_id=workspace.id,
        user_id=user.id,
    )

    assert result is not None
    assert result.id == workspace.id


def test_get_by_id_and_user_returns_none_for_wrong_user(
    db_session,
    user,
    user_factory,
):
    repository = WorkspaceRepository(db_session)

    workspace = Workspace(
        user_id=user.id,
        name="Test Workspace",
    )

    db_session.add(workspace)
    db_session.flush()

    another_user = user_factory()

    result = repository.get_by_id_and_user(
        workspace_id=workspace.id,
        user_id=another_user.id,
    )

    assert result is None


def test_get_by_id_and_user_returns_none_for_unknown_workspace(
    db_session,
    user,
):
    repository = WorkspaceRepository(db_session)

    result = repository.get_by_id_and_user(
        workspace_id=uuid4(),
        user_id=user.id,
    )

    assert result is None


def test_list_by_user(db_session, user):
    repository = WorkspaceRepository(db_session)

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

    result = repository.list_by_user(user.id)

    assert len(result) == 2
    assert {workspace.name for workspace in result} == {
        "Workspace One",
        "Workspace Two",
    }


def test_list_by_user_does_not_return_other_users_workspaces(
    db_session,
    user,
    user_factory,
):
    repository = WorkspaceRepository(db_session)

    another_user = user_factory()

    workspace_one = Workspace(
        user_id=user.id,
        name="My Workspace",
    )

    workspace_two = Workspace(
        user_id=another_user.id,
        name="Other Workspace",
    )

    db_session.add_all(
        [
            workspace_one,
            workspace_two,
        ]
    )
    db_session.flush()

    result = repository.list_by_user(user.id)

    assert len(result) == 1
    assert result[0].name == "My Workspace"


def test_exists_by_name_and_user_returns_true(
    db_session,
    user,
):
    repository = WorkspaceRepository(db_session)

    workspace = Workspace(
        user_id=user.id,
        name="Existing Workspace",
    )

    db_session.add(workspace)
    db_session.flush()

    assert repository.exists_by_name_and_user(
        user_id=user.id,
        name="Existing Workspace",
    )


def test_exists_by_name_and_user_returns_false_for_different_user(
    db_session,
    user,
    user_factory,
):
    repository = WorkspaceRepository(db_session)

    another_user = user_factory()

    workspace = Workspace(
        user_id=user.id,
        name="Existing Workspace",
    )

    db_session.add(workspace)
    db_session.flush()

    assert not repository.exists_by_name_and_user(
        user_id=another_user.id,
        name="Existing Workspace",
    )


def test_exists_by_name_and_user_is_case_sensitive(
    db_session,
    user,
):
    repository = WorkspaceRepository(db_session)

    workspace = Workspace(
        user_id=user.id,
        name="My Workspace",
    )

    db_session.add(workspace)
    db_session.flush()

    assert repository.exists_by_name_and_user(
        user_id=user.id,
        name="My Workspace",
    )

    assert not repository.exists_by_name_and_user(
        user_id=user.id,
        name="my workspace",
    )


def test_delete_workspace(db_session, user):
    repository = WorkspaceRepository(db_session)

    workspace = Workspace(
        user_id=user.id,
        name="Workspace To Delete",
    )

    db_session.add(workspace)
    db_session.flush()

    repository.delete(workspace)

    db_session.flush()

    result = repository.get_by_id_and_user(
        workspace.id,
        user.id,
    )

    assert result is None
