from datetime import timedelta

from app.models.chat_message import ChatMessage
from app.models.enums import MessageRole
from app.repositories.chat_message_repository import ChatMessageRepository


def test_create_message(db_session, chat):
    repository = ChatMessageRepository(db_session)

    message = ChatMessage(
        chat_id=chat.id,
        role=MessageRole.USER,
        content="Hello, AI!",
    )

    result = repository.create(message)

    assert result is message
    assert result.id is not None
    assert result.chat_id == chat.id
    assert result.role == MessageRole.USER
    assert result.content == "Hello, AI!"


def test_list_by_chat_returns_messages(
    db_session,
    chat,
    chat_message_factory,
):
    repository = ChatMessageRepository(db_session)

    message_1 = chat_message_factory(
        content="First message",
    )
    message_2 = chat_message_factory(
        content="Second message",
    )

    result = repository.list_by_chat(chat.id)

    assert len(result) == 2
    assert result[0].id == message_1.id
    assert result[1].id == message_2.id


def test_list_by_chat_orders_by_created_at_ascending(
    db_session,
    chat,
    chat_message_factory,
):
    repository = ChatMessageRepository(db_session)

    message_1 = chat_message_factory(
        content="Older message",
    )
    message_2 = chat_message_factory(
        content="Newer message",
    )

    # Explicitly control timestamps so the test does not depend
    # on how quickly the two records were created.
    message_1.created_at = message_2.created_at - timedelta(minutes=1)

    db_session.flush()

    result = repository.list_by_chat(chat.id)

    assert result[0].id == message_1.id
    assert result[1].id == message_2.id


def test_list_by_chat_returns_empty_for_chat_without_messages(
    db_session,
    chat,
):
    repository = ChatMessageRepository(db_session)

    result = repository.list_by_chat(chat.id)

    assert result == []


def test_list_recent_returns_limited_messages(
    db_session,
    chat,
    chat_message_factory,
):
    repository = ChatMessageRepository(db_session)

    messages = [chat_message_factory(content=f"Message {i}") for i in range(5)]

    for index, message in enumerate(messages):
        message.created_at = messages[0].created_at + timedelta(minutes=index)

    db_session.flush()

    result = repository.list_recent(
        chat.id,
        limit=3,
    )

    assert len(result) == 3

    expected_ids = [
        messages[2].id,
        messages[3].id,
        messages[4].id,
    ]

    assert [message.id for message in result] == expected_ids


def test_list_recent_returns_messages_in_chronological_order(
    db_session,
    chat,
    chat_message_factory,
):
    repository = ChatMessageRepository(db_session)

    messages = [chat_message_factory(content=f"Message {i}") for i in range(5)]

    for index, message in enumerate(messages):
        message.created_at = messages[0].created_at + timedelta(minutes=index)

    db_session.flush()

    result = repository.list_recent(
        chat.id,
        limit=3,
    )

    assert [message.id for message in result] == [
        messages[2].id,
        messages[3].id,
        messages[4].id,
    ]


def test_list_recent_returns_all_messages_when_limit_exceeds_count(
    db_session,
    chat,
    chat_message_factory,
):
    repository = ChatMessageRepository(db_session)

    messages = [chat_message_factory(content=f"Message {i}") for i in range(3)]

    result = repository.list_recent(
        chat.id,
        limit=10,
    )

    assert len(result) == 3

    assert {message.id for message in result} == {message.id for message in messages}


def test_list_recent_returns_empty_for_chat_without_messages(
    db_session,
    chat,
):
    repository = ChatMessageRepository(db_session)

    result = repository.list_recent(
        chat.id,
        limit=5,
    )

    assert result == []
