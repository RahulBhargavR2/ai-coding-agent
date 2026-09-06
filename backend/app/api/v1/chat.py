from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies.auth import CurrentActiveUser
from app.dependencies.chat import ChatServiceDep
from app.models.chat import Chat
from app.schemas.chat import (
    ChatAnswerResponse,
    ChatCreateRequest,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatResponse,
    ChatSourceResponse,
)
from app.services.chat.chat_service import ChatService


router = APIRouter(
    prefix="/chats",
    tags=["Chat"],
)


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_chat(
    data: ChatCreateRequest,
    chat_service: ChatServiceDep,
    current_user: CurrentActiveUser
) -> ChatResponse:
    """
    Create a new coding conversation for a repository.
    """

    chat = chat_service.create_chat(
        user_id=current_user.id,
        repository_id=data.repository_id,
        title=data.title,
    )

    return ChatResponse(
        id=chat.id,
        repository_id=chat.repository_id,
        title=chat.title,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
    )


@router.get(
    "/{chat_id}",
    response_model=ChatResponse,
)
def get_chat(
    chat_id: UUID,
    current_user: CurrentActiveUser,
    chat_service: ChatServiceDep
) -> ChatResponse:
    """
    Retrieve a chat owned by the current user.
    """

    chat = chat_service.get_chat(
        chat_id=chat_id,
        user_id=current_user.id,
    )

    return ChatResponse(
        id=chat.id,
        repository_id=chat.repository_id,
        title=chat.title,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
    )


@router.post(
    "/{chat_id}/messages",
    response_model=ChatAnswerResponse,
)
def send_message(
    chat_id: UUID,
    data: ChatMessageRequest,
    current_user: CurrentActiveUser,
    chat_service: ChatServiceDep
) -> ChatAnswerResponse:
    """
    Send a message to the context-aware coding assistant.
    """

    result = chat_service.send_message(
        chat_id=chat_id,
        user_id=current_user.id,
        content=data.content,
    )

    return ChatAnswerResponse(
        chat_id=result.chat_id,
        message_id=result.message_id,
        content=result.content,
        sources=[
            ChatSourceResponse(
                path=source["path"],
                language=source["language"],
                start_line=source["start_line"],
                end_line=source["end_line"],
                symbol=source["symbol"],
                score=source["score"],
            )
            for source in result.sources
        ],
    )


@router.get(
    "/{chat_id}/messages",
    response_model=list[ChatMessageResponse],
)
def list_messages(
    chat_id: UUID,
    current_user: CurrentActiveUser,
    chat_service: ChatServiceDep
) -> list[ChatMessageResponse]:
    """
    Retrieve the messages belonging to a chat.
    """

    chat_service.get_chat(
        chat_id=chat_id,
        user_id=current_user.id,
    )

    messages = chat_service.list_messages(
        chat_id=chat_id,
    )

    return [
        ChatMessageResponse(
            id=message.id,
            chat_id=message.chat_id,
            role=message.role,
            content=message.content,
            created_at=message.created_at,
        )
        for message in messages
    ]


@router.get(
    "/repository/{repository_id}",
    response_model=list[ChatResponse],
)
def list_repository_chats(
    repository_id: UUID,
    current_user: CurrentActiveUser,
    chat_service: ChatServiceDep,
) -> list[ChatResponse]:
    """
    List all chats belonging to a repository.
    """

    chats = chat_service.list_repository_chats(
        user_id=current_user.id,
        repository_id=repository_id,
    )

    return [
        ChatResponse(
            id=chat.id,
            repository_id=chat.repository_id,
            title=chat.title,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
        )
        for chat in chats
    ]
