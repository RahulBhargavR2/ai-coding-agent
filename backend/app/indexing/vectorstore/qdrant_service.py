from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.indexing.embeddings.models import EmbeddingResult
from app.indexing.vectorstore.collections import QdrantCollectionConfig


@dataclass(frozen=True)
class VectorPoint:
    """
    Represents a vector and its searchable metadata.
    """

    id: str
    embedding: EmbeddingResult
    payload: dict[str, Any]


@dataclass(frozen=True)
class VectorSearchResult:
    """
    Represents a Qdrant similarity-search result.
    """

    id: str
    score: float
    payload: dict[str, Any]


class QdrantService:
    """
    Provides repository indexing and semantic-search operations
    against Qdrant.

    This class is intentionally isolated from the application's
    SQLAlchemy models.
    """

    def __init__(
        self,
        client: QdrantClient,
        collection: QdrantCollectionConfig,
    ) -> None:
        self.client = client
        self.collection = collection

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    def ensure_collection(self) -> None:
        """
        Create the configured collection if it does not already exist.
        """

        if self.client.collection_exists(
            collection_name=self.collection.name,
        ):
            return

        self.client.create_collection(
            collection_name=self.collection.name,
            vectors_config=models.VectorParams(
                size=self.collection.vector_dimension,
                distance=self._distance(),
            ),
        )

    def collection_exists(self) -> bool:
        """
        Check whether the configured collection exists.
        """

        return self.client.collection_exists(
            collection_name=self.collection.name,
        )

    # ------------------------------------------------------------------
    # Upsert
    # ------------------------------------------------------------------

    def upsert(
        self,
        points: Sequence[VectorPoint],
    ) -> None:
        """
        Insert or update vector points.

        The collection is created automatically if necessary.
        """

        if not points:
            return

        self.ensure_collection()

        qdrant_points = [
            models.PointStruct(
                id=self._normalize_point_id(point.id),
                vector=list(point.embedding.vector),
                payload=point.payload,
            )
            for point in points
        ]

        self.client.upsert(
            collection_name=self.collection.name,
            points=qdrant_points,
        )

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        query_vector: Sequence[float],
        limit: int = 10,
        repository_id: UUID | None = None,
    ) -> list[VectorSearchResult]:
        """
        Perform semantic similarity search.

        Args:
            query_vector:
                Embedding vector for the search query.

            limit:
                Maximum number of results.

            repository_id:
                Optional repository filter.

        Returns:
            Ranked Qdrant search results.
        """

        if limit <= 0:
            raise ValueError("limit must be greater than zero.")

        if not self.collection_exists():
            return []

        query_filter = None

        if repository_id is not None:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="repository_id",
                        match=models.MatchValue(value=str(repository_id)),
                    )
                ]
            )

        results = self.client.query_points(
            collection_name=self.collection.name,
            query=list(query_vector),
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )

        return [
            VectorSearchResult(
                id=str(result.id),
                score=result.score,
                payload=result.payload or {},
            )
            for result in results.points
        ]

    # ------------------------------------------------------------------
    # Repository deletion
    # ------------------------------------------------------------------

    def delete_repository(
        self,
        repository_id: UUID,
    ) -> None:
        """
        Delete all vectors belonging to a repository.
        """

        if not self.collection_exists():
            return

        self.client.delete(
            collection_name=self.collection.name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="repository_id",
                            match=models.MatchValue(value=str(repository_id)),
                        )
                    ]
                )
            ),
        )

    # ------------------------------------------------------------------
    # Point deletion
    # ------------------------------------------------------------------

    def delete_points(
        self,
        point_ids: Sequence[str],
    ) -> None:
        """
        Delete specific vector points.
        """

        if not point_ids:
            return

        if not self.collection_exists():
            return

        self.client.delete(
            collection_name=self.collection.name,
            points_selector=models.PointIdsList(
                points=[self._normalize_point_id(point_id) for point_id in point_ids]
            ),
        )
    
    def delete_file(
    self,
    repository_file_id: UUID,
    ) -> None:
        """
        Delete all vectors belonging to a repository file.
        """

        if not self.collection_exists():
            return

        self.client.delete(
            collection_name=self.collection.name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="repository_file_id",
                            match=models.MatchValue(
                                value=str(repository_file_id),
                            ),
                        ),
                    ],
                ),
            ),
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _distance(self) -> models.Distance:
        """
        Convert the configured distance name into a Qdrant enum.
        """

        distance_map = {
            "Cosine": models.Distance.COSINE,
            "Dot": models.Distance.DOT,
            "Euclid": models.Distance.EUCLID,
            "Manhattan": models.Distance.MANHATTAN,
        }

        try:
            return distance_map[self.collection.distance]
        except KeyError as exc:
            raise ValueError(
                f"Unsupported Qdrant distance: " f"{self.collection.distance}"
            ) from exc

    @staticmethod
    def _normalize_point_id(
        point_id: str,
    ) -> str | int:
        """
        Normalize point IDs accepted by Qdrant.

        UUID strings are converted to UUID objects where possible.
        Other identifiers remain strings.
        """

        try:
            return str(UUID(point_id))
        except ValueError:
            return point_id
