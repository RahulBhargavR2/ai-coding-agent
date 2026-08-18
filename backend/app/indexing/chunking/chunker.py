from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Chunk:
    """
    Represents a searchable unit of repository content.

    A chunk is the unit that will eventually be embedded and indexed
    in the vector store and BM25 index.
    """

    content: str

    chunk_type: str

    language: str | None

    start_line: int | None

    end_line: int | None

    symbol_name: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)


class Chunker(ABC):
    """
    Base interface for repository content chunkers.

    Specialized implementations such as CodeChunker and
    MarkdownChunker provide the actual chunking strategy.
    """

    @abstractmethod
    def chunk(
        self,
        content: str,
        language: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[Chunk]:
        """
        Split content into searchable chunks.

        Args:
            content: Source content.
            language: Detected language.
            metadata: Optional contextual metadata.

        Returns:
            List of searchable chunks.
        """
        raise NotImplementedError
