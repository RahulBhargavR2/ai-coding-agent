from uuid import uuid4

from app.repositories.chat_repository import ChatRepository


def test_create_chat(db_session, chat):
    repository = ChatRepository(db_session)

    result = repository.create(chat)

    assert result is chat
    assert result.id == chat.id
    assert result.repository_id == chat.repository_id
    assert result.title == chat.title


def test_get_by_id(db_session, chat):
    repository = ChatRepository(db_session)

    result = repository.get_by_id(chat.id)

    assert result is not None
    assert result.id == chat.id
    assert result.repository_id == chat.repository_id
    assert result.title == chat.title


def test_get_by_id_returns_none_when_not_found(db_session):
    repository = ChatRepository(db_session)

    result = repository.get_by_id(uuid4())

    assert result is None


def test_get_by_id_and_user_returns_chat(
    db_session,
    chat,
    user,
):
    repository = ChatRepository(db_session)

    result = repository.get_by_id_and_user(
        chat_id=chat.id,
        user_id=user.id,
    )

    assert result is not None
    assert result.id == chat.id


def test_get_by_id_and_user_returns_none_for_wrong_user(
    db_session,
    chat,
    user_factory,
):
    repository = ChatRepository(db_session)

    another_user = user_factory(
        email="another@example.com",
    )

    result = repository.get_by_id_and_user(
        chat_id=chat.id,
        user_id=another_user.id,
    )

    assert result is None


def test_list_by_repository(
    db_session,
    repository,
    chat_factory,
    user,
):
    chat_repo = ChatRepository(db_session)

    chat_1 = chat_factory(title="Chat 1")
    chat_2 = chat_factory(title="Chat 2")

    result = chat_repo.list_by_repository(
        repository_id=repository.id,
        user_id=user.id,
    )

    assert len(result) == 2

    chat_ids = {chat.id for chat in result}

    assert chat_1.id in chat_ids
    assert chat_2.id in chat_ids


def test_list_by_repository_returns_empty_for_wrong_user(
    db_session,
    repository,
    chat,
    user_factory,
):
    chat_repo = ChatRepository(db_session)

    another_user = user_factory(
        email="another@example.com",
    )

    result = chat_repo.list_by_repository(
        repository_id=repository.id,
        user_id=another_user.id,
    )

    assert result == []


def test_list_by_repository_orders_by_updated_at_desc(
    db_session,
    repository,
    chat_factory,
    user,
):
    chat_repo = ChatRepository(db_session)

    older_chat = chat_factory(title="Older Chat")
    newer_chat = chat_factory(title="Newer Chat")

    older_chat.updated_at = older_chat.updated_at.replace(
        year=2020,
    )
    newer_chat.updated_at = newer_chat.updated_at.replace(
        year=2025,
    )

    db_session.flush()

    result = chat_repo.list_by_repository(
        repository_id=repository.id,
        user_id=user.id,
    )

    assert result[0].id == newer_chat.id
    assert result[1].id == older_chat.id
