from __future__ import annotations

from typing import Annotated
from functools import lru_cache

from fastapi import Depends

from app.core.config import settings
from app.dependencies.uow import UnitOfWorkDep

from app.indexing.embeddings.embedding_service import EmbeddingService
from app.indexing.embeddings.models import EmbeddingConfig, EmbeddingProvider

from app.retrieval.hybrid_retriever import HybridRetriever
from app.services.chat.chat_service import ChatService
from app.services.chat.context_builder import ContextBuilder, ContextConfig

from app.dependencies.llm import LLMServiceDEP

from app.dependencies.indexing import (
    get_embedding_service,
    get_bm25_service,
    get_qdrant_service,
    get_retriever,
)


def get_chat_service(
    uow: UnitOfWorkDep,
    retriever: HybridRetriever = Depends(get_retriever),
    *,
    llm_service: LLMServiceDEP,
) -> ChatService:
    """
    Compose the application-level ChatService.
    """

    return ChatService(
        retriever=retriever,
        context_builder=ContextBuilder(config=ContextConfig()),
        llm_service=llm_service,
        uow=uow,
    )


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
