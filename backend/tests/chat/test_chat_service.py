from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.core.exceptions import (
    BusinessValidationError,
    ChatNotFound,
)
from app.models.enums import MessageRole
from app.retrieval.models import (
    RetrievedChunk,
    RetrievalResult,
)
from app.services.chat.chat_service import (
    ChatService,
    ChatResponse,
)
from app.services.chat.context_builder import (
    ContextBuilder,
    ConversationContext,
)
from app.services.chat.llm_service import (
    LLMResponse,
)


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def repository_id():
    return uuid4()


@pytest.fixture
def chat_id():
    return uuid4()


@pytest.fixture
def chat(
    chat_id,
    user_id,
    repository_id,
):
    return SimpleNamespace(
        id=chat_id,
        user_id=user_id,
        repository_id=repository_id,
        title="Test Chat",
    )


@pytest.fixture
def uow():
    uow = Mock()

    uow.chats = Mock()
    uow.chat_messages = Mock()

    return uow


@pytest.fixture
def retriever():
    return Mock()


@pytest.fixture
def context_builder():
    return Mock()


@pytest.fixture
def llm_service():
    return Mock()


@pytest.fixture
def service(
    uow,
    retriever,
    context_builder,
    llm_service,
):
    return ChatService(
        retriever=retriever,
        context_builder=context_builder,
        llm_service=llm_service,
        uow=uow,
    )


def make_chunk():
    return RetrievedChunk(
        id="chunk-1",
        content="def hello(): pass",
        score=1.0,
        relative_path="app/main.py",
        language="python",
        start_line=1,
        end_line=2,
        symbol_name="hello",
        metadata={},
    )


def test_create_chat(
    service,
    uow,
    user_id,
    repository_id,
):
    created_chat = SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        repository_id=repository_id,
        title="My Chat",
    )

    uow.chats.create.return_value = created_chat

    result = service.create_chat(
        user_id=user_id,
        repository_id=repository_id,
        title="My Chat",
    )

    assert result == created_chat

    created = uow.chats.create.call_args.args[0]


    assert created.repository_id == repository_id
    assert created.title == "My Chat"

    uow.commit.assert_called_once()
    uow.refresh.assert_called_once_with(created_chat)


def test_get_chat_success(
    service,
    uow,
    chat,
    user_id,
    chat_id,
):
    uow.chats.get_by_id_and_user.return_value = chat

    result = service.get_chat(
        chat_id=chat_id,
        user_id=user_id,
    )

    assert result == chat

    uow.chats.get_by_id_and_user.assert_called_once_with(
        chat_id=chat_id,
        user_id=user_id,
    )


def test_get_chat_raises_when_missing(
    service,
    uow,
    user_id,
    chat_id,
):
    uow.chats.get_by_id_and_user.return_value = None

    with pytest.raises(ChatNotFound):
        service.get_chat(
            chat_id=chat_id,
            user_id=user_id,
        )


def test_send_message_rejects_empty_content(
    service,
):
    with pytest.raises(
        BusinessValidationError,
        match="Message content cannot be empty",
    ):
        service.send_message(
            chat_id=uuid4(),
            user_id=uuid4(),
            content="   ",
        )


def test_send_message_persists_user_message(
    service,
    uow,
    retriever,
    context_builder,
    llm_service,
    chat,
    user_id,
):
    uow.chats.get_chat.return_value = chat

    user_message = SimpleNamespace(
        id=uuid4(),
        chat_id=chat.id,
        role=MessageRole.USER,
        content="Explain authentication",
    )

    assistant_message = SimpleNamespace(
        id=uuid4(),
        chat_id=chat.id,
        role=MessageRole.ASSISTANT,
        content="Authentication uses JWT.",
    )

    uow.chat_messages.create.side_effect = [
        user_message,
        assistant_message,
    ]

    uow.chat_messages.list_recent.return_value = []

    retrieval_result = RetrievalResult(
        query="Explain authentication",
        chunks=[make_chunk()],
    )

    retriever.retrieve.return_value = retrieval_result

    context = ConversationContext(
        history=[],
        chunks=retrieval_result.chunks,
        formatted_repository_context=("File: app/main.py"),
    )

    context_builder.config.max_history_messages = 12
    context_builder.config.max_context_chunks = 8

    context_builder.build.return_value = context

    llm_service.build_llm_messages.return_value = []

    llm_service.generate.return_value = LLMResponse(content="Authentication uses JWT.")

    result = service.send_message(
        chat_id=chat.id,
        user_id=user_id,
        content="  Explain authentication  ",
    )

    assert isinstance(result, ChatResponse)

    assert result.chat_id == chat.id
    assert result.message_id == assistant_message.id
    assert result.content == ("Authentication uses JWT.")

    assert len(result.sources) == 1

    assert result.sources[0] == {
        "path": "app/main.py",
        "language": "python",
        "start_line": 1,
        "end_line": 2,
        "symbol": "hello",
        "score": 1.0,
    }

    first_message = uow.chat_messages.create.call_args_list[0].args[0]

    assert first_message.role == MessageRole.USER
    assert first_message.content == ("Explain authentication")


def test_send_message_calls_retriever(
    service,
    uow,
    retriever,
    context_builder,
    llm_service,
    chat,
    user_id,
):
    uow.chats.get_chat.return_value = chat

    user_message = SimpleNamespace(
        id=uuid4(),
        chat_id=chat.id,
        role=MessageRole.USER,
        content="Find authentication",
    )

    assistant_message = SimpleNamespace(
        id=uuid4(),
        chat_id=chat.id,
        role=MessageRole.ASSISTANT,
        content="Answer",
    )

    uow.chat_messages.create.side_effect = [
        user_message,
        assistant_message,
    ]

    uow.chat_messages.list_recent.return_value = []

    retrieval_result = RetrievalResult(
        query="Find authentication",
        chunks=[],
    )

    retriever.retrieve.return_value = retrieval_result

    context_builder.config.max_history_messages = 12
    context_builder.config.max_context_chunks = 8

    context_builder.build.return_value = ConversationContext(
        history=[],
        chunks=[],
        formatted_repository_context="",
    )

    llm_service.build_llm_messages.return_value = []

    llm_service.generate.return_value = LLMResponse(content="Answer")

    service.send_message(
        chat_id=chat.id,
        user_id=user_id,
        content="Find authentication",
    )

    retrieval_query = retriever.retrieve.call_args.args[0]

    assert retrieval_query.query == ("Find authentication")

    assert retrieval_query.repository_id == chat.repository_id

    assert retrieval_query.limit == 8


def test_send_message_builds_context(
    service,
    uow,
    retriever,
    context_builder,
    llm_service,
    chat,
    user_id,
):
    uow.chats.get_chat.return_value = chat

    user_message = SimpleNamespace(
        id=uuid4(),
        chat_id=chat.id,
        role=MessageRole.USER,
        content="Explain code",
    )

    assistant_message = SimpleNamespace(
        id=uuid4(),
        chat_id=chat.id,
        role=MessageRole.ASSISTANT,
        content="Answer",
    )

    uow.chat_messages.create.side_effect = [
        user_message,
        assistant_message,
    ]

    history = [
        user_message,
    ]

    uow.chat_messages.list_recent.return_value = history

    retrieval_result = RetrievalResult(
        query="Explain code",
        chunks=[make_chunk()],
    )

    retriever.retrieve.return_value = retrieval_result

    context_builder.config.max_history_messages = 12
    context_builder.config.max_context_chunks = 8

    context = ConversationContext(
        history=history,
        chunks=retrieval_result.chunks,
        formatted_repository_context="context",
    )

    context_builder.build.return_value = context

    llm_service.build_llm_messages.return_value = []

    llm_service.generate.return_value = LLMResponse(content="Answer")

    service.send_message(
        chat_id=chat.id,
        user_id=user_id,
        content="Explain code",
    )

    context_builder.build.assert_called_once_with(
        history=history,
        chunks=retrieval_result.chunks,
    )


def test_send_message_builds_llm_request(
    service,
    uow,
    retriever,
    context_builder,
    llm_service,
    chat,
    user_id,
):
    uow.chats.get_chat.return_value = chat

    user_message = SimpleNamespace(
        id=uuid4(),
        chat_id=chat.id,
        role=MessageRole.USER,
        content="Explain code",
    )

    assistant_message = SimpleNamespace(
        id=uuid4(),
        chat_id=chat.id,
        role=MessageRole.ASSISTANT,
        content="Answer",
    )

    uow.chat_messages.create.side_effect = [
        user_message,
        assistant_message,
    ]

    uow.chat_messages.list_recent.return_value = []

    retriever.retrieve.return_value = RetrievalResult(
        query="Explain code",
        chunks=[],
    )

    context_builder.config.max_history_messages = 12
    context_builder.config.max_context_chunks = 8

    context = ConversationContext(
        history=[],
        chunks=[],
        formatted_repository_context="",
    )

    context_builder.build.return_value = context

    messages = [
        SimpleNamespace(
            role="user",
            content="Explain code",
        )
    ]

    llm_service.build_llm_messages.return_value = messages

    llm_service.generate.return_value = LLMResponse(content="Answer")

    service.send_message(
        chat_id=chat.id,
        user_id=user_id,
        content="Explain code",
    )

    llm_service.build_llm_messages.assert_called_once()

    request = llm_service.generate.call_args.args[0]

    assert request.messages == messages
    assert request.temperature == 0.2


def test_send_message_persists_assistant_message(
    service,
    uow,
    retriever,
    context_builder,
    llm_service,
    chat,
    user_id,
):
    uow.chats.get_chat.return_value = chat

    user_message = SimpleNamespace(
        id=uuid4(),
        chat_id=chat.id,
        role=MessageRole.USER,
        content="Hello",
    )

    assistant_message = SimpleNamespace(
        id=uuid4(),
        chat_id=chat.id,
        role=MessageRole.ASSISTANT,
        content="Hello back",
    )

    uow.chat_messages.create.side_effect = [
        user_message,
        assistant_message,
    ]

    uow.chat_messages.list_recent.return_value = []

    retriever.retrieve.return_value = RetrievalResult(
        query="Hello",
        chunks=[],
    )

    context_builder.config.max_history_messages = 12
    context_builder.config.max_context_chunks = 8

    context_builder.build.return_value = ConversationContext(
        history=[],
        chunks=[],
        formatted_repository_context="",
    )

    llm_service.build_llm_messages.return_value = []

    llm_service.generate.return_value = LLMResponse(content="Hello back")

    result = service.send_message(
        chat_id=chat.id,
        user_id=user_id,
        content="Hello",
    )

    persisted_assistant = uow.chat_messages.create.call_args_list[1].args[0]

    assert persisted_assistant.role == MessageRole.ASSISTANT

    assert persisted_assistant.content == "Hello back"

    assert result.content == "Hello back"

    assert uow.commit.call_count == 2


def test_send_message_propagates_retrieval_failure(
    service,
    uow,
    retriever,
    chat,
    user_id,
):
    uow.chats.get_chat.return_value = chat

    user_message = SimpleNamespace(
        id=uuid4(),
        chat_id=chat.id,
        role=MessageRole.USER,
        content="Find code",
    )

    uow.chat_messages.create.return_value = user_message
    uow.chat_messages.list_recent.return_value = []

    retriever.retrieve.side_effect = RuntimeError("retrieval failed")

    with pytest.raises(
        RuntimeError,
        match="retrieval failed",
    ):
        service.send_message(
            chat_id=chat.id,
            user_id=user_id,
            content="Find code",
        )


def test_send_message_propagates_llm_failure(
    service,
    uow,
    retriever,
    context_builder,
    llm_service,
    chat,
    user_id,
):
    uow.chats.get_chat.return_value = chat

    user_message = SimpleNamespace(
        id=uuid4(),
        chat_id=chat.id,
        role=MessageRole.USER,
        content="Find code",
    )

    uow.chat_messages.create.return_value = user_message
    uow.chat_messages.list_recent.return_value = []

    retriever.retrieve.return_value = RetrievalResult(
        query="Find code",
        chunks=[],
    )

    context_builder.config.max_history_messages = 12
    context_builder.config.max_context_chunks = 8

    context_builder.build.return_value = ConversationContext(
        history=[],
        chunks=[],
        formatted_repository_context="",
    )

    llm_service.build_llm_messages.return_value = []

    llm_service.generate.side_effect = RuntimeError("llm failed")

    with pytest.raises(
        RuntimeError,
        match="llm failed",
    ):
        service.send_message(
            chat_id=chat.id,
            user_id=user_id,
            content="Find code",
        )


def test_source_from_chunk():
    chunk = make_chunk()

    result = ChatService._source_from_chunk(chunk)

    assert result == {
        "path": "app/main.py",
        "language": "python",
        "start_line": 1,
        "end_line": 2,
        "symbol": "hello",
        "score": 1.0,
    }
