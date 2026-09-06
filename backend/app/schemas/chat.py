from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import MessageRole


class ChatCreateRequest(BaseModel):
    repository_id: UUID
    title: str | None = Field(
        default=None,
        max_length=200,
    )


class ChatResponse(BaseModel):
    id: UUID
    repository_id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


class ChatMessageRequest(BaseModel):
    content: str = Field(
        min_length=1,
        max_length=20_000,
    )


class ChatMessageResponse(BaseModel):
    id: UUID
    chat_id: UUID
    role: MessageRole
    content: str
    created_at: datetime


class ChatAnswerResponse(BaseModel):
    chat_id: UUID
    message_id: UUID
    content: str
    sources: list["ChatSourceResponse"]


class ChatSourceResponse(BaseModel):
    path: str
    language: str | None
    start_line: int | None
    end_line: int | None
    symbol: str | None
    score: float
