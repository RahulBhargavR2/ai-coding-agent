from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QdrantCollectionConfig:
    """
    Configuration for a Qdrant collection.
    """

    name: str

    vector_dimension: int

    distance: str = "Cosine"


class CollectionNames:
    """
    Centralized names for Qdrant collections.
    """

    CODE = "repository_code"
