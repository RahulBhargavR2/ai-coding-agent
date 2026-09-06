from uuid import uuid4

import pytest

from app.indexing.bm25.bm25_service import (
    BM25Document,
    BM25Service,
)


@pytest.fixture
def documents():
    repository_id = uuid4()

    return [
        BM25Document(
            id="1",
            content="authentication login service",
            payload={
                "repository_id": str(repository_id),
                "repository_file_id": "file-1",
            },
        ),
        BM25Document(
            id="2",
            content="database repository service",
            payload={
                "repository_id": str(repository_id),
                "repository_file_id": "file-2",
            },
        ),
        BM25Document(
            id="3",
            content="authentication token refresh",
            payload={
                "repository_id": str(repository_id),
                "repository_file_id": "file-3",
            },
        ),
    ]


def test_build_creates_index(documents):
    service = BM25Service()

    service.build(documents)

    assert service.document_count() == 3


def test_build_empty_documents(service=None):
    service = BM25Service()

    service.build([])

    assert service.document_count() == 0
    assert service.search("anything") == []


def test_search_returns_relevant_documents(documents):
    service = BM25Service()
    service.build(documents)

    results = service.search(
        "authentication",
    )

    assert len(results) == 2

    result_ids = {result.id for result in results}

    assert "1" in result_ids
    assert "3" in result_ids


def test_search_respects_limit(documents):
    service = BM25Service()
    service.build(documents)

    results = service.search(
        "service",
        limit=1,
    )

    assert len(results) == 1


def test_search_rejects_invalid_limit(documents):
    service = BM25Service()
    service.build(documents)

    with pytest.raises(
        ValueError,
        match="limit must be greater than zero",
    ):
        service.search(
            "service",
            limit=0,
        )


def test_search_empty_query_returns_empty(documents):
    service = BM25Service()
    service.build(documents)

    assert service.search("   ") == []


def test_search_filters_by_repository(documents):
    service = BM25Service()

    other_repository = uuid4()

    documents.append(
        BM25Document(
            id="4",
            content="authentication login",
            payload={
                "repository_id": str(other_repository),
                "repository_file_id": "file-4",
            },
        )
    )

    service.build(documents)

    results = service.search(
        "authentication",
        repository_id=other_repository,
    )

    assert len(results) == 1
    assert results[0].id == "4"


def test_add_documents(documents):
    service = BM25Service()

    service.build(documents[:1])

    assert service.document_count() == 1

    service.add(documents[1:])

    assert service.document_count() == 3


def test_add_empty_documents_does_nothing(documents):
    service = BM25Service()

    service.build(documents)

    service.add([])

    assert service.document_count() == 3


def test_delete_file(documents):
    service = BM25Service()
    service.build(documents)

    service.delete_file(uuid4())

    # No document has that UUID, so nothing should change.
    assert service.document_count() == 3


def test_delete_file_removes_matching_document(documents):
    service = BM25Service()
    service.build(documents)

    file_id = uuid4()

    documents.append(
        BM25Document(
            id="4",
            content="temporary document",
            payload={
                "repository_id": str(uuid4()),
                "repository_file_id": str(file_id),
            },
        )
    )

    service.build(documents)

    assert service.document_count() == 4

    service.delete_file(file_id)

    assert service.document_count() == 3


def test_delete_repository(documents):
    service = BM25Service()

    repository_id = uuid4()

    documents = [
        BM25Document(
            id="1",
            content="authentication",
            payload={
                "repository_id": str(repository_id),
            },
        ),
        BM25Document(
            id="2",
            content="database",
            payload={
                "repository_id": str(uuid4()),
            },
        ),
    ]

    service.build(documents)

    service.delete_repository(repository_id)

    assert service.document_count() == 1
