from unittest.mock import Mock

import pytest

from app.indexing.chunking.chunker import Chunk
from app.indexing.embeddings.embedding_service import EmbeddingService
from app.indexing.embeddings.models import (
    EmbeddingConfig,
    EmbeddingProvider,
)


@pytest.fixture
def config():
    return EmbeddingConfig(
        provider=EmbeddingProvider.SENTENCE_TRANSFORMERS,
        model_name="test-model",
        dimension=3,
        batch_size=2,
        normalize_embeddings=True,
    )


@pytest.fixture
def embedding_service(config, monkeypatch):
    model = Mock()

    model.encode.return_value = [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
    ]

    monkeypatch.setattr(
        EmbeddingService,
        "_load_model",
        lambda self: model,
    )

    service = EmbeddingService(config)

    return service


def test_embed_returns_one_embedding_per_chunk(
    embedding_service,
):
    chunks = [
        Chunk(
            content="hello",
            chunk_type="function",
            language="python",
            start_line=1,
            end_line=2,
            symbol_name="hello",
            metadata={},
        ),
        Chunk(
            content="world",
            chunk_type="function",
            language="python",
            start_line=4,
            end_line=5,
            symbol_name="world",
            metadata={},
        ),
    ]

    results = embedding_service.embed(chunks)

    assert len(results) == 2

    assert results[0].vector == (0.1, 0.2, 0.3)
    assert results[1].vector == (0.4, 0.5, 0.6)

    assert results[0].dimension == 3
    assert results[0].model_name == "test-model"


def test_embed_empty_chunks_returns_empty_list(
    embedding_service,
):
    result = embedding_service.embed([])

    assert result == []


def test_embed_query_rejects_empty_query(
    embedding_service,
):
    with pytest.raises(
        ValueError,
        match="query must not be empty",
    ):
        embedding_service.embed_query("   ")


def test_embed_query_returns_vector(
    embedding_service,
):
    embedding_service._model.encode.return_value = [
        0.1,
        0.2,
        0.3,
    ]

    result = embedding_service.embed_query("authentication service")

    assert result == (0.1, 0.2, 0.3)


def test_embed_batch_returns_batch_metadata(
    embedding_service,
):
    chunks = [
        Chunk(
            content="hello",
            chunk_type="function",
            language="python",
            start_line=1,
            end_line=1,
            symbol_name="hello",
            metadata={},
        ),
        Chunk(
            content="world",
            chunk_type="function",
            language="python",
            start_line=2,
            end_line=2,
            symbol_name="world",
            metadata={},
        ),
    ]

    result = embedding_service.embed_batch(chunks)

    assert result.count == 2
    assert result.dimension == 3
    assert result.model_name == "test-model"
    assert len(result.embeddings) == 2


def test_dimension_returns_configured_dimension(
    embedding_service,
):
    assert embedding_service.dimension() == 3


def test_model_name_returns_configured_model(
    embedding_service,
):
    assert embedding_service.model_name() == "test-model"


def test_embedding_dimension_mismatch_raises(
    embedding_service,
):
    embedding_service._model.encode.return_value = [
        [0.1, 0.2],
    ]

    chunks = [
        Chunk(
            content="hello",
            chunk_type="function",
            language="python",
            start_line=1,
            end_line=1,
            symbol_name="hello",
            metadata={},
        ),
    ]

    with pytest.raises(
        ValueError,
        match="Embedding dimension mismatch",
    ):
        embedding_service.embed(chunks)
