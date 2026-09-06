from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class RetrievalQuery:
    """
    Represents a repository-aware retrieval request.
    """

    query: str
    repository_id: UUID
    limit: int = 10


@dataclass(frozen=True)
class RetrievedChunk:
    """
    Represents a piece of repository context returned by retrieval.
    """

    id: str
    content: str
    score: float
    relative_path: str
    language: str | None
    start_line: int | None
    end_line: int | None
    symbol_name: str | None
    metadata: dict[str, Any]


@dataclass(frozen=True)
class RetrievalResult:
    """
    Represents the complete retrieval response.
    """

    query: str
    chunks: list[RetrievedChunk]
