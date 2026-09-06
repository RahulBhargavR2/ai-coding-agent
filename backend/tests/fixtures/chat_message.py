import pytest
from uuid import UUID

from app.models.chat_message import ChatMessage
from app.models.enums import MessageRole


@pytest.fixture
def chat_message_factory(db_session, chat):
    """
    Factory for creating ChatMessage instances.
    """

    def factory(
        *,
        chat_id: UUID | None = None,
        role: MessageRole = MessageRole.USER,
        content: str = "Hello",
        model_name: str | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
        message_metadata: dict | None = None,
    ) -> ChatMessage:
        message = ChatMessage(
            chat_id=(chat.id if chat_id is None else chat_id),
            role=role,
            content=content,
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            message_metadata=message_metadata,
        )

        db_session.add(message)
        db_session.flush()

        return message

    return factory


@pytest.fixture
def chat_message(chat_message_factory):
    return chat_message_factory()
