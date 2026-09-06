from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import Mock

import pytest

from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.models import (
    RetrievedChunk,
    RetrievalQuery,
)


@pytest.fixture
def repository_id():
    return uuid4()


@pytest.fixture
def qdrant_service():
    return Mock()


@pytest.fixture
def bm25_service():
    return Mock()


@pytest.fixture
def embedding_service():
    return Mock()


@pytest.fixture
def retriever(
    qdrant_service,
    bm25_service,
    embedding_service,
):
    return HybridRetriever(
        qdrant_service=qdrant_service,
        bm25_service=bm25_service,
        embedding_service=embedding_service,
    )


def make_result(
    result_id: str,
    score: float,
    content: str = "def hello(): pass",
    path: str = "app/main.py",
):
    return SimpleNamespace(
        id=result_id,
        score=score,
        payload={
            "content": content,
            "relative_path": path,
            "language": "python",
            "start_line": 1,
            "end_line": 2,
            "symbol_name": "hello",
        },
    )


# ======================================================================
# Semantic search
# ======================================================================


def test_semantic_search_embeds_query(
    retriever,
    embedding_service,
    qdrant_service,
    repository_id,
):
    query = RetrievalQuery(
        query="find hello function",
        repository_id=repository_id,
        limit=5,
    )

    embedding_service.embed_query.return_value = [
        0.1,
        0.2,
        0.3,
    ]

    qdrant_service.search.return_value = []

    result = retriever._semantic_search(query)

    embedding_service.embed_query.assert_called_once_with("find hello function")

    qdrant_service.search.assert_called_once_with(
        query_vector=[0.1, 0.2, 0.3],
        limit=5,
        repository_id=repository_id,
    )

    assert result == []


def test_semantic_search_returns_qdrant_results(
    retriever,
    embedding_service,
    qdrant_service,
    repository_id,
):
    query = RetrievalQuery(
        query="authentication",
        repository_id=repository_id,
        limit=3,
    )

    embedding_service.embed_query.return_value = [0.1, 0.2]

    expected = [
        make_result("chunk-1", 0.9),
        make_result("chunk-2", 0.7),
    ]

    qdrant_service.search.return_value = expected

    result = retriever._semantic_search(query)

    assert result == expected


# ======================================================================
# Lexical search
# ======================================================================


def test_lexical_search_calls_bm25(
    retriever,
    bm25_service,
    repository_id,
):
    query = RetrievalQuery(
        query="database connection",
        repository_id=repository_id,
        limit=5,
    )

    expected = [
        make_result("chunk-1", 4.5),
    ]

    bm25_service.search.return_value = expected

    result = retriever._lexical_search(query)

    bm25_service.search.assert_called_once_with(
        query="database connection",
        limit=5,
        repository_id=repository_id,
    )

    assert result == expected


# ======================================================================
# Result conversion
# ======================================================================


def test_to_chunk_converts_result():
    result = make_result(
        result_id="abc",
        score=0.75,
        content="class User: pass",
        path="app/user.py",
    )

    chunk = HybridRetriever._to_chunk(
        result=result,
        score=0.8,
    )

    assert isinstance(chunk, RetrievedChunk)

    assert chunk.id == "abc"
    assert chunk.content == "class User: pass"
    assert chunk.score == 0.8
    assert chunk.relative_path == "app/user.py"
    assert chunk.language == "python"
    assert chunk.start_line == 1
    assert chunk.end_line == 2
    assert chunk.symbol_name == "hello"

    assert chunk.metadata == result.payload


def test_to_chunk_handles_missing_payload_fields():
    result = SimpleNamespace(
        id="abc",
        score=0.5,
        payload={},
    )

    chunk = HybridRetriever._to_chunk(
        result=result,
        score=0.5,
    )

    assert chunk.id == "abc"
    assert chunk.content == ""
    assert chunk.relative_path == ""
    assert chunk.language is None
    assert chunk.start_line is None
    assert chunk.end_line is None
    assert chunk.symbol_name is None
    assert chunk.metadata == {}


# ======================================================================
# Merge
# ======================================================================


def test_merge_results_normalizes_semantic_scores(
    retriever,
):
    semantic_results = [
        make_result("a", 0.9),
        make_result("b", 0.45),
    ]

    lexical_results = []

    result = retriever._merge_results(
        semantic_results=semantic_results,
        lexical_results=lexical_results,
        limit=10,
    )

    assert len(result) == 2

    assert result[0].id == "a"
    assert result[0].score == pytest.approx(1.0)

    assert result[1].id == "b"
    assert result[1].score == pytest.approx(0.5)


def test_merge_results_normalizes_lexical_scores(
    retriever,
):
    semantic_results = []

    lexical_results = [
        make_result("a", 10.0),
        make_result("b", 5.0),
    ]

    result = retriever._merge_results(
        semantic_results=semantic_results,
        lexical_results=lexical_results,
        limit=10,
    )

    assert len(result) == 2

    assert result[0].id == "a"
    assert result[0].score == pytest.approx(1.0)

    assert result[1].id == "b"
    assert result[1].score == pytest.approx(0.5)


def test_merge_results_combines_duplicate_chunks(
    retriever,
):
    semantic_results = [
        make_result("same", 0.8),
    ]

    lexical_results = [
        make_result("same", 4.0),
    ]

    result = retriever._merge_results(
        semantic_results=semantic_results,
        lexical_results=lexical_results,
        limit=10,
    )

    assert len(result) == 1

    assert result[0].id == "same"

    # Both normalized scores are 1.0.
    assert result[0].score == pytest.approx(2.0)


def test_merge_results_removes_duplicates(
    retriever,
):
    semantic_results = [
        make_result("same", 0.9),
    ]

    lexical_results = [
        make_result("same", 5.0),
    ]

    result = retriever._merge_results(
        semantic_results=semantic_results,
        lexical_results=lexical_results,
        limit=10,
    )

    assert len(result) == 1


def test_merge_results_sorts_by_score(
    retriever,
):
    semantic_results = [
        make_result("a", 0.3),
        make_result("b", 0.9),
    ]

    lexical_results = [
        make_result("c", 5.0),
    ]

    result = retriever._merge_results(
        semantic_results=semantic_results,
        lexical_results=lexical_results,
        limit=10,
    )

    assert [chunk.id for chunk in result] == [
        "b",
        "c",
        "a",
    ]


def test_merge_results_respects_limit(
    retriever,
):
    semantic_results = [
        make_result("a", 0.9),
        make_result("b", 0.8),
        make_result("c", 0.7),
    ]

    result = retriever._merge_results(
        semantic_results=semantic_results,
        lexical_results=[],
        limit=2,
    )

    assert len(result) == 2

    assert [chunk.id for chunk in result] == [
        "a",
        "b",
    ]


def test_merge_results_with_empty_results(
    retriever,
):
    result = retriever._merge_results(
        semantic_results=[],
        lexical_results=[],
        limit=10,
    )

    assert result == []


# ======================================================================
# Full retrieve
# ======================================================================


def test_retrieve_combines_semantic_and_lexical_results(
    retriever,
    embedding_service,
    qdrant_service,
    bm25_service,
    repository_id,
):
    query = RetrievalQuery(
        query="authentication",
        repository_id=repository_id,
        limit=5,
    )

    embedding_service.embed_query.return_value = [
        0.1,
        0.2,
    ]

    qdrant_service.search.return_value = [
        make_result("semantic", 0.9),
    ]

    bm25_service.search.return_value = [
        make_result("lexical", 5.0),
    ]

    result = retriever.retrieve(query)

    assert result.query == "authentication"

    assert len(result.chunks) == 2

    assert {chunk.id for chunk in result.chunks} == {
        "semantic",
        "lexical",
    }

    embedding_service.embed_query.assert_called_once()
    qdrant_service.search.assert_called_once()
    bm25_service.search.assert_called_once()


def test_retrieve_preserves_limit(
    retriever,
    embedding_service,
    qdrant_service,
    bm25_service,
    repository_id,
):
    query = RetrievalQuery(
        query="authentication",
        repository_id=repository_id,
        limit=2,
    )

    embedding_service.embed_query.return_value = [0.1]

    qdrant_service.search.return_value = [
        make_result("a", 0.9),
        make_result("b", 0.8),
    ]

    bm25_service.search.return_value = [
        make_result("c", 5.0),
        make_result("d", 4.0),
    ]

    result = retriever.retrieve(query)

    assert len(result.chunks) == 2


def test_retrieve_propagates_embedding_error(
    retriever,
    embedding_service,
    repository_id,
):
    query = RetrievalQuery(
        query="authentication",
        repository_id=repository_id,
    )

    embedding_service.embed_query.side_effect = RuntimeError("embedding failed")

    with pytest.raises(
        RuntimeError,
        match="embedding failed",
    ):
        retriever.retrieve(query)


def test_retrieve_propagates_qdrant_error(
    retriever,
    embedding_service,
    qdrant_service,
    repository_id,
):
    query = RetrievalQuery(
        query="authentication",
        repository_id=repository_id,
    )

    embedding_service.embed_query.return_value = [0.1]

    qdrant_service.search.side_effect = RuntimeError("qdrant failed")

    with pytest.raises(
        RuntimeError,
        match="qdrant failed",
    ):
        retriever.retrieve(query)


def test_retrieve_propagates_bm25_error(
    retriever,
    embedding_service,
    qdrant_service,
    bm25_service,
    repository_id,
):
    query = RetrievalQuery(
        query="authentication",
        repository_id=repository_id,
    )

    embedding_service.embed_query.return_value = [0.1]

    qdrant_service.search.return_value = []

    bm25_service.search.side_effect = RuntimeError("bm25 failed")

    with pytest.raises(
        RuntimeError,
        match="bm25 failed",
    ):
        retriever.retrieve(query)
