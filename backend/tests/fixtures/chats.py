import pytest
from uuid import UUID

from app.models.chat import Chat


@pytest.fixture
def chat_factory(db_session, repository):
    """
    Factory for creating Chat instances.
    """

    def factory(
        *,
        repository_id: UUID | None = None,
        title: str = "Test Chat",
    ) -> Chat:
        chat = Chat(
            repository_id=(repository.id if repository_id is None else repository_id),
            title=title,
        )

        db_session.add(chat)
        db_session.flush()

        return chat

    return factory


@pytest.fixture
def chat(chat_factory):
    return chat_factory()
