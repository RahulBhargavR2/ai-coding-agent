import pytest

from uuid import UUID

from app.models.workspace import Workspace


@pytest.fixture
def workspace_factory(db_session, user) -> Workspace:
    """
    Factory for creating Workspace instances.
    """

    def factory(
        *,
        user_id : UUID | None = None,
        name: str ="Test Workspace",
        description: str = "Sample description",
    ):
        workspace = Workspace(
            user_id=user.id if user_id is None else user_id,
            name=name,
            description=description,
        )

        db_session.add(workspace)
        db_session.flush()

        return workspace

    return factory


@pytest.fixture
def workspace(workspace_factory):
    return workspace_factory()
