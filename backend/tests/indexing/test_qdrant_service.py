from unittest.mock import Mock
from uuid import uuid4

import pytest
from qdrant_client.http import models

from app.indexing.embeddings.models import EmbeddingResult
from app.indexing.vectorstore.qdrant_service import (
    QdrantService,
    VectorPoint,
)
from app.indexing.vectorstore.collections import QdrantCollectionConfig


@pytest.fixture
def collection():
    return QdrantCollectionConfig(
        name="test_collection",
        vector_dimension=3,
        distance="Cosine",
    )


@pytest.fixture
def qdrant_client():
    return Mock()


@pytest.fixture
def service(qdrant_client, collection):
    return QdrantService(
        client=qdrant_client,
        collection=collection,
    )


def test_collection_exists(service, qdrant_client):
    qdrant_client.collection_exists.return_value = True

    assert service.collection_exists() is True

    qdrant_client.collection_exists.assert_called_once_with(
        collection_name="test_collection",
    )


def test_ensure_collection_does_nothing_if_exists(
    service,
    qdrant_client,
):
    qdrant_client.collection_exists.return_value = True

    service.ensure_collection()

    qdrant_client.create_collection.assert_not_called()


def test_ensure_collection_creates_missing_collection(
    service,
    qdrant_client,
):
    qdrant_client.collection_exists.return_value = False

    service.ensure_collection()

    qdrant_client.create_collection.assert_called_once()

    kwargs = qdrant_client.create_collection.call_args.kwargs

    assert kwargs["collection_name"] == "test_collection"

    vector_config = kwargs["vectors_config"]

    assert vector_config.size == 3
    assert vector_config.distance == models.Distance.COSINE


def test_upsert_empty_points_does_nothing(
    service,
    qdrant_client,
):
    service.upsert([])

    qdrant_client.upsert.assert_not_called()


def test_upsert_creates_qdrant_points(
    service,
    qdrant_client,
):
    qdrant_client.collection_exists.return_value = True

    point = VectorPoint(
        id="point-1",
        embedding=EmbeddingResult(
            vector=(0.1, 0.2, 0.3),
            model_name="test",
            dimension=3,
        ),
        payload={
            "repository_id": "repo-1",
        },
    )

    service.upsert([point])

    qdrant_client.upsert.assert_called_once()

    kwargs = qdrant_client.upsert.call_args.kwargs

    assert kwargs["collection_name"] == "test_collection"

    qdrant_points = kwargs["points"]

    assert len(qdrant_points) == 1
    assert qdrant_points[0].vector == [0.1, 0.2, 0.3]
    assert qdrant_points[0].payload == {
        "repository_id": "repo-1",
    }


def test_search_rejects_invalid_limit(
    service,
):
    with pytest.raises(
        ValueError,
        match="limit must be greater than zero",
    ):
        service.search(
            query_vector=[0.1, 0.2, 0.3],
            limit=0,
        )


def test_search_returns_empty_if_collection_missing(
    service,
    qdrant_client,
):
    qdrant_client.collection_exists.return_value = False

    result = service.search(
        query_vector=[0.1, 0.2, 0.3],
    )

    assert result == []

    qdrant_client.query_points.assert_not_called()


def test_search_returns_results(
    service,
    qdrant_client,
):
    qdrant_client.collection_exists.return_value = True

    qdrant_result = Mock()
    qdrant_result.id = "point-1"
    qdrant_result.score = 0.95
    qdrant_result.payload = {
        "repository_id": "repo-1",
        "content": "authentication",
    }

    response = Mock()
    response.points = [qdrant_result]

    qdrant_client.query_points.return_value = response

    result = service.search(
        query_vector=[0.1, 0.2, 0.3],
    )

    assert len(result) == 1

    assert result[0].id == "point-1"
    assert result[0].score == 0.95
    assert result[0].payload["content"] == "authentication"


def test_search_applies_repository_filter(
    service,
    qdrant_client,
):
    qdrant_client.collection_exists.return_value = True

    response = Mock()
    response.points = []

    qdrant_client.query_points.return_value = response

    repository_id = uuid4()

    service.search(
        query_vector=[0.1, 0.2, 0.3],
        repository_id=repository_id,
    )

    kwargs = qdrant_client.query_points.call_args.kwargs

    query_filter = kwargs["query_filter"]

    assert query_filter is not None
    assert len(query_filter.must) == 1

    condition = query_filter.must[0]

    assert condition.key == "repository_id"
    assert condition.match.value == str(repository_id)


def test_delete_points_does_nothing_for_empty_list(
    service,
    qdrant_client,
):
    service.delete_points([])

    qdrant_client.delete.assert_not_called()


def test_delete_repository_does_nothing_if_collection_missing(
    service,
    qdrant_client,
):
    qdrant_client.collection_exists.return_value = False

    service.delete_repository(uuid4())

    qdrant_client.delete.assert_not_called()


def test_delete_file_does_nothing_if_collection_missing(
    service,
    qdrant_client,
):
    qdrant_client.collection_exists.return_value = False

    service.delete_file(uuid4())

    qdrant_client.delete.assert_not_called()


def test_normalize_uuid_point_id():
    point_id = str(uuid4())

    result = QdrantService._normalize_point_id(point_id)

    assert result == point_id


def test_normalize_non_uuid_point_id():
    result = QdrantService._normalize_point_id("repository-file:0")

    assert result == "repository-file:0"


def test_invalid_distance_raises(
    service,
):
    service.collection = Mock(distance="invalid")

    with pytest.raises(
        ValueError,
        match="Unsupported Qdrant distance",
    ):
        service._distance()
