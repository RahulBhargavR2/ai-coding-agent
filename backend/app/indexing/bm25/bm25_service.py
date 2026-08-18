from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from rank_bm25 import BM25Okapi


@dataclass(frozen=True)
class BM25Document:
    """
    Represents a searchable document in the BM25 index.
    """

    id: str
    content: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class BM25SearchResult:
    """
    Represents a BM25 search result.
    """

    id: str
    score: float
    payload: dict[str, Any]


class BM25Service:
    """
    Provides lexical retrieval over repository chunks.

    BM25 is kept independent from Qdrant so that the hybrid
    retrieval layer can combine both retrieval strategies later.
    """

    def __init__(self) -> None:
        self._documents: list[BM25Document] = []
        self._index: BM25Okapi | None = None

    # ------------------------------------------------------------------
    # Index construction
    # ------------------------------------------------------------------

    def build(
        self,
        documents: list[BM25Document],
    ) -> None:
        """
        Build the BM25 index from repository documents.
        """

        self._documents = list(documents)

        if not self._documents:
            self._index = None
            return

        tokenized_documents = [
            self._tokenize(document.content) for document in self._documents
        ]

        self._index = BM25Okapi(tokenized_documents)

    # ------------------------------------------------------------------
    # Add documents
    # ------------------------------------------------------------------

    def add(
        self,
        documents: list[BM25Document],
    ) -> None:
        """
        Add documents to the existing BM25 index.

        Since BM25Okapi does not provide an efficient incremental
        update API, the index is rebuilt after adding documents.
        """

        if not documents:
            return

        self.build(
            [
                *self._documents,
                *documents,
            ]
        )

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        limit: int = 10,
        repository_id: UUID | None = None,
    ) -> list[BM25SearchResult]:
        """
        Search the BM25 index.

        Args:
            query:
                User search query.

            limit:
                Maximum number of results.

            repository_id:
                Optional repository scope.

        Returns:
            Ranked lexical-search results.
        """

        if limit <= 0:
            raise ValueError("limit must be greater than zero.")

        if self._index is None:
            return []

        query_tokens = self._tokenize(query)

        if not query_tokens:
            return []

        scores = self._index.get_scores(query_tokens)

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda index: scores[index],
            reverse=True,
        )

        results: list[BM25SearchResult] = []

        for index in ranked_indices:
            score = float(scores[index])

            if score <= 0:
                continue

            document = self._documents[index]

            if repository_id is not None and document.payload.get(
                "repository_id"
            ) != str(repository_id):
                continue

            results.append(
                BM25SearchResult(
                    id=document.id,
                    score=score,
                    payload=document.payload,
                )
            )

            if len(results) >= limit:
                break

        return results

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_repository(
        self,
        repository_id: UUID,
    ) -> None:
        """
        Remove all documents belonging to a repository.
        """

        repository_id_value = str(repository_id)

        remaining_documents = [
            document
            for document in self._documents
            if document.payload.get("repository_id") != repository_id_value
        ]

        self.build(remaining_documents)

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def document_count(self) -> int:
        """
        Return the number of indexed BM25 documents.
        """

        return len(self._documents)

    # ------------------------------------------------------------------
    # Tokenization
    # ------------------------------------------------------------------

    @staticmethod
    def _tokenize(
        text: str,
    ) -> list[str]:
        """
        Tokenize source code and natural-language content.

        Code identifiers are split on common separators while
        retaining useful identifier fragments.
        """

        normalized = (
            text.replace("::", " ")
            .replace("->", " ")
            .replace("=>", " ")
            .replace("/", " ")
            .replace("\\", " ")
            .replace(".", " ")
            .replace(",", " ")
            .replace("(", " ")
            .replace(")", " ")
            .replace("[", " ")
            .replace("]", " ")
            .replace("{", " ")
            .replace("}", " ")
            .replace(":", " ")
            .replace(";", " ")
        )

        tokens: list[str] = []

        for token in normalized.lower().split():
            if not token:
                continue

            tokens.append(token)

            # Preserve useful pieces of snake_case identifiers.
            if "_" in token:
                tokens.extend(part for part in token.split("_") if part)

            # Preserve useful pieces of kebab-case identifiers.
            if "-" in token:
                tokens.extend(part for part in token.split("-") if part)

        return tokens
