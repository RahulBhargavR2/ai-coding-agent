from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.core.exceptions import ChatNotFound, BusinessValidationError, RepositoryNotFound
from app.models.chat import Chat
from app.models.chat_message import ChatMessage
from app.models.enums import MessageRole
from app.repositories.chat_message_repository import (
    ChatMessageRepository,
)
from app.repositories.chat_repository import ChatRepository
from app.retrieval.models import RetrievalQuery
from app.retrieval.retriever import Retriever
from app.services.chat.context_builder import ContextBuilder
from app.services.chat.llm_service import (
    LLMRequest,
    LLMService
)
from app.services.chat.prompts import (
    CODING_ASSISTANT_SYSTEM_PROMPT,
)
from app.dependencies.uow import UnitOfWorkDep


@dataclass(frozen=True)
class ChatResponse:
    """
    Represents the response returned by the chat service.
    """

    chat_id: UUID
    message_id: UUID
    content: str
    sources: list[dict]


class ChatService:
    """
    Application service responsible for context-aware coding chat.
    """

    def __init__(
        self,
        retriever: Retriever,
        context_builder: ContextBuilder,
        llm_service: LLMService,
        uow=UnitOfWorkDep,
    ) -> None:
        self.uow = uow
        self.retriever = retriever
        self.context_builder = context_builder
        self.llm_service = llm_service

    # ==================================================================
    # Chat lifecycle
    # ==================================================================

    def create_chat(
        self,
        user_id:UUID,
        repository_id: UUID,
        title: str | None = None,
    ) -> Chat:
        """
        Create a new coding conversation.
        """

        repository = self.uow.repositories.get_by_id_and_user(user_id=user_id,repository_id=repository_id)

        if repository is None:
            raise RepositoryNotFound("Repository is not found")

        chat = Chat(
            repository_id=repository_id,
            title=title,
        )

        chat = self.uow.chats.create(chat)
        self.uow.commit()
        self.uow.refresh(chat)

        return chat

    def get_chat(
        self,
        chat_id: UUID,
        user_id: UUID,
    ) -> Chat:
        """
        Retrieve a chat belonging to the current user.
        """

        chat = self.uow.chats.get_by_id_and_user(
            chat_id=chat_id,
            user_id=user_id,
        )

        if chat is None:
            raise ChatNotFound(f"Chat {chat_id} not found.")

        return chat

    # ==================================================================
    # Messaging
    # ==================================================================

    def send_message(
        self,
        chat_id: UUID,
        user_id: UUID,
        content: str,
    ) -> ChatResponse:
        """
        Send a message through the context-aware coding assistant.
        """

        content = content.strip()

        if not content:
            raise BusinessValidationError("Message content cannot be empty.")

        chat = self.uow.chats.get_chat(
            chat_id=chat_id,
            user_id=user_id,
        )

        # --------------------------------------------------------------
        # Persist user message
        # --------------------------------------------------------------

        user_message = ChatMessage(
            chat_id=chat.id,
            role=MessageRole.USER,
            content=content,
        )

        user_message = self.uow.chat_messages.create(user_message)
        self.uow.commit()
        self.uow.refresh(user_message)
        # --------------------------------------------------------------
        # Load conversation history
        # --------------------------------------------------------------

        history = self.uow.chat_messages.list_recent(
            chat_id=chat.id,
            limit=self.context_builder.config.max_history_messages,
        )

        # --------------------------------------------------------------
        # Retrieve repository context
        # --------------------------------------------------------------

        retrieval_result = self.retriever.retrieve(
            RetrievalQuery(
                query=content,
                repository_id=chat.repository_id,
                limit=self.context_builder.config.max_context_chunks,
            )
        )

        # --------------------------------------------------------------
        # Build context
        # --------------------------------------------------------------

        context = self.context_builder.build(
            history=history,
            chunks=retrieval_result.chunks,
        )

        # --------------------------------------------------------------
        # Build LLM request
        # --------------------------------------------------------------

        messages = self.llm_service.build_llm_messages(
            system_prompt=CODING_ASSISTANT_SYSTEM_PROMPT,
            history=context.history,
            repository_context=(context.formatted_repository_context),
            user_message=content,
        )

        request = LLMRequest(
            messages=messages,
            temperature=0.2,
        )

        # --------------------------------------------------------------
        # Generate response
        # --------------------------------------------------------------

        response = self.llm_service.generate(request)

        # --------------------------------------------------------------
        # Persist assistant message
        # --------------------------------------------------------------

        assistant_message = ChatMessage(
            chat_id=chat.id,
            role=MessageRole.ASSISTANT,
            content=response.content,
        )

        assistant_message = self.uow.chat_messages.create(assistant_message)
        self.uow.commit()
        self.uow.refresh(assistant_message)

        return ChatResponse(
            chat_id=chat.id,
            message_id=assistant_message.id,
            content=response.content,
            sources=[self._source_from_chunk(chunk) for chunk in context.chunks],
        )


    def list_repository_chats(
        self,
        repository_id:UUID,
        user_id:UUID
    )->list[ChatResponse]:

        """
        Returns all the chats belonging to a user and repository
        """

        chats = self.uow.chats.list_by_repository(
            repository_id,
            user_id
        )

        if chats is None:
            raise ChatNotFound("Chats not found")
        
        return chats


    
    def list_messages(self,chat_id:UUID):
        """
        Lists all the messages related to a chat
        """
        messages = self.uow.chat_messages.list_by_chat(chat_id)

        if messages is None:
            raise ChatNotFound("Chat not found")

        return messages


    # ==================================================================
    # Helpers
    # ==================================================================

    @staticmethod
    def _source_from_chunk(
        chunk,
    ) -> dict:
        """
        Convert a retrieved chunk into a user-visible source.
        """

        return {
            "path": chunk.relative_path,
            "language": chunk.language,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
            "symbol": chunk.symbol_name,
            "score": chunk.score,
        }
