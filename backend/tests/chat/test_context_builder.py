from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.models.enums import MessageRole
from app.services.chat.context_builder import (
    ContextBuilder,
    ContextConfig,
)
from app.retrieval.models import RetrievedChunk


def make_message(content: str, role=MessageRole.USER):
    return SimpleNamespace(
        id=uuid4(),
        chat_id=uuid4(),
        role=role,
        content=content,
        created_at=datetime.now(timezone.utc),
    )


def make_chunk(
    chunk_id: str,
    score: float,
    content: str,
):
    return RetrievedChunk(
        id=chunk_id,
        content=content,
        score=score,
        relative_path="app/main.py",
        language="python",
        start_line=1,
        end_line=10,
        symbol_name="hello",
        metadata={},
    )


def test_select_history_keeps_recent_messages():
    builder = ContextBuilder(
        ContextConfig(
            max_history_messages=2,
        )
    )

    history = [
        make_message("one"),
        make_message("two"),
        make_message("three"),
    ]

    result = builder._select_history(history)

    assert [message.content for message in result] == [
        "two",
        "three",
    ]


def test_select_history_returns_empty_when_limit_zero():
    builder = ContextBuilder(
        ContextConfig(
            max_history_messages=0,
        )
    )

    result = builder._select_history([make_message("hello")])

    assert result == []


def test_select_chunks_sorts_by_score():
    builder = ContextBuilder()

    chunks = [
        make_chunk("a", 0.2, "low"),
        make_chunk("b", 0.9, "high"),
        make_chunk("c", 0.5, "medium"),
    ]

    result = builder._select_chunks(chunks)

    assert [chunk.id for chunk in result] == [
        "b",
        "c",
        "a",
    ]


def test_select_chunks_respects_max_chunks():
    builder = ContextBuilder(
        ContextConfig(
            max_context_chunks=2,
        )
    )

    chunks = [
        make_chunk("a", 0.9, "a"),
        make_chunk("b", 0.8, "b"),
        make_chunk("c", 0.7, "c"),
    ]

    result = builder._select_chunks(chunks)

    assert len(result) == 2


def test_select_chunks_truncates_large_chunk():
    builder = ContextBuilder(
        ContextConfig(
            max_chunk_characters=5,
        )
    )

    chunk = make_chunk(
        "a",
        1.0,
        "1234567890",
    )

    result = builder._select_chunks([chunk])

    assert result[0].content == "12345"


def test_select_chunks_respects_total_character_limit():
    builder = ContextBuilder(
        ContextConfig(
            max_chunk_characters=100,
            max_total_context_characters=10,
        )
    )

    chunks = [
        make_chunk("a", 1.0, "123456"),
        make_chunk("b", 0.9, "78901"),
    ]

    result = builder._select_chunks(chunks)

    assert len(result) == 1


def test_select_chunks_returns_empty_when_limit_zero():
    builder = ContextBuilder(
        ContextConfig(
            max_context_chunks=0,
        )
    )

    result = builder._select_chunks([make_chunk("a", 1.0, "hello")])

    assert result == []


def test_format_location_with_start_and_end():
    chunk = make_chunk("a", 1.0, "hello")

    assert ContextBuilder._format_location(chunk) == "1-10"


def test_format_location_with_only_start():
    chunk = make_chunk("a", 1.0, "hello")

    chunk = RetrievedChunk(
        id=chunk.id,
        content=chunk.content,
        score=chunk.score,
        relative_path=chunk.relative_path,
        language=chunk.language,
        start_line=5,
        end_line=None,
        symbol_name=chunk.symbol_name,
        metadata=chunk.metadata,
    )

    assert ContextBuilder._format_location(chunk) == "5"


def test_format_location_without_line_numbers():
    chunk = RetrievedChunk(
        id="a",
        content="hello",
        score=1.0,
        relative_path="app/main.py",
        language="python",
        start_line=None,
        end_line=None,
        symbol_name=None,
        metadata={},
    )

    assert ContextBuilder._format_location(chunk) == "unknown"


def test_format_chunks_returns_empty_string_for_no_chunks():
    builder = ContextBuilder()

    assert builder._format_chunks([]) == ""


def test_format_chunks_contains_metadata():
    builder = ContextBuilder()

    chunk = make_chunk(
        "a",
        1.0,
        "def hello():\n    pass",
    )

    result = builder._format_chunks([chunk])

    assert "[Context 1]" in result
    assert "File: app/main.py" in result
    assert "Language: python" in result
    assert "Location: 1-10" in result
    assert "Symbol: hello" in result
    assert "def hello():" in result


def test_build_returns_history_chunks_and_formatted_context():
    builder = ContextBuilder()

    history = [
        make_message("hello"),
    ]

    chunks = [
        make_chunk("a", 1.0, "def hello(): pass"),
    ]

    result = builder.build(
        history=history,
        chunks=chunks,
    )

    assert result.history == history
    assert len(result.chunks) == 1
    assert "def hello(): pass" in (result.formatted_repository_context)
