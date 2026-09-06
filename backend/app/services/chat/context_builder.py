from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from app.models.chat_message import ChatMessage
from app.retrieval.models import RetrievedChunk


@dataclass(frozen=True)
class ContextConfig:
    """
    Controls how much conversational and repository context
    can be included in an LLM request.
    """

    max_history_messages: int = 12
    max_context_chunks: int = 8
    max_chunk_characters: int = 12_000
    max_total_context_characters: int = 60_000


@dataclass(frozen=True)
class ConversationContext:
    """
    Represents the prepared context passed to the LLM layer.
    """

    history: list[ChatMessage]
    chunks: list[RetrievedChunk]
    formatted_repository_context: str


class ContextBuilder:
    """
    Builds controlled LLM context from conversation history
    and repository retrieval results.
    """

    def __init__(
        self,
        config: ContextConfig | None = None,
    ) -> None:
        self.config = config or ContextConfig()

    def build(
        self,
        history: Sequence[ChatMessage],
        chunks: Sequence[RetrievedChunk],
    ) -> ConversationContext:
        """
        Build the context used by the LLM.
        """

        selected_history = self._select_history(history)

        selected_chunks = self._select_chunks(chunks)

        formatted_context = self._format_chunks(selected_chunks)

        return ConversationContext(
            history=selected_history,
            chunks=selected_chunks,
            formatted_repository_context=formatted_context,
        )

    # ------------------------------------------------------------------
    # Conversation history
    # ------------------------------------------------------------------

    def _select_history(
        self,
        history: Sequence[ChatMessage],
    ) -> list[ChatMessage]:
        """
        Keep only the most recent conversation messages.
        """

        if self.config.max_history_messages <= 0:
            return []

        return list(history[-self.config.max_history_messages :])

    # ------------------------------------------------------------------
    # Retrieved chunks
    # ------------------------------------------------------------------

    def _select_chunks(
        self,
        chunks: Sequence[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        """
        Select the highest-ranked retrieved chunks.
        """

        if self.config.max_context_chunks <= 0:
            return []

        ranked_chunks = sorted(
            chunks,
            key=lambda chunk: chunk.score,
            reverse=True,
        )

        selected: list[RetrievedChunk] = []
        total_characters = 0

        for chunk in ranked_chunks:
            if len(selected) >= self.config.max_context_chunks:
                break

            content = chunk.content

            if len(content) > self.config.max_chunk_characters:
                content = content[: self.config.max_chunk_characters]

            if (
                total_characters + len(content)
                > self.config.max_total_context_characters
            ):
                break

            selected.append(
                RetrievedChunk(
                    id=chunk.id,
                    content=content,
                    score=chunk.score,
                    relative_path=chunk.relative_path,
                    language=chunk.language,
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                    symbol_name=chunk.symbol_name,
                    metadata=chunk.metadata,
                )
            )

            total_characters += len(content)

        return selected

    # ------------------------------------------------------------------
    # Formatting
    # ------------------------------------------------------------------

    def _format_chunks(
        self,
        chunks: Sequence[RetrievedChunk],
    ) -> str:
        """
        Format retrieved repository chunks into LLM-readable context.
        """

        if not chunks:
            return ""

        sections: list[str] = []

        for index, chunk in enumerate(
            chunks,
            start=1,
        ):
            location = self._format_location(chunk)

            sections.append(
                "\n".join(
                    [
                        f"[Context {index}]",
                        f"File: {chunk.relative_path}",
                        f"Language: {chunk.language or 'unknown'}",
                        f"Location: {location}",
                        (f"Symbol: " f"{chunk.symbol_name or 'unknown'}"),
                        "",
                        chunk.content,
                    ]
                )
            )

        return "\n\n".join(sections)

    @staticmethod
    def _format_location(
        chunk: RetrievedChunk,
    ) -> str:
        """
        Format source line information.
        """

        if chunk.start_line is not None and chunk.end_line is not None:
            return f"{chunk.start_line}-" f"{chunk.end_line}"

        if chunk.start_line is not None:
            return str(chunk.start_line)

        return "unknown"
