from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence


class EmbeddingProvider(str, Enum):
    """
    Supported embedding providers.
    """

    SENTENCE_TRANSFORMERS = "sentence_transformers"


@dataclass(frozen=True)
class EmbeddingConfig:
    """
    Configuration required to generate embeddings.
    """

    provider: EmbeddingProvider

    model_name: str

    dimension: int

    batch_size: int = 32

    normalize_embeddings: bool = True


@dataclass(frozen=True)
class EmbeddingResult:
    """
    Represents the embedding generated for a single chunk.
    """

    vector: tuple[float, ...]

    model_name: str

    dimension: int


@dataclass(frozen=True)
class BatchEmbeddingResult:
    """
    Represents embeddings generated for a batch of chunks.
    """

    embeddings: tuple[EmbeddingResult, ...]

    model_name: str

    dimension: int

    count: int
