from __future__ import annotations

from collections.abc import Sequence

from sentence_transformers import SentenceTransformer

from app.indexing.chunking.chunker import Chunk
from app.indexing.embeddings.models import (
    BatchEmbeddingResult,
    EmbeddingConfig,
    EmbeddingProvider,
    EmbeddingResult,
)


class EmbeddingService:
    """
    Generates vector embeddings for repository chunks.

    Responsibilities:
    - Load the configured embedding model.
    - Generate embeddings in batches.
    - Normalize embeddings when configured.
    - Validate embedding dimensions.
    - Convert model output into application-level results.

    This class does not:
    - Persist embeddings.
    - Communicate with Qdrant.
    - Perform similarity search.
    """

    def __init__(
        self,
        config: EmbeddingConfig,
    ) -> None:
        self.config = config
        self._model = self._load_model()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def embed(
        self,
        chunks: Sequence[Chunk],
    ) -> list[EmbeddingResult]:
        """
        Generate an embedding for each chunk.

        Args:
            chunks: Repository chunks to embed.

        Returns:
            One EmbeddingResult for each input chunk.
        """

        if not chunks:
            return []

        texts = [chunk.content for chunk in chunks]

        embeddings = self._model.encode(
            texts,
            batch_size=self.config.batch_size,
            normalize_embeddings=self.config.normalize_embeddings,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        results: list[EmbeddingResult] = []

        for vector in embeddings:
            embedding = tuple(float(value) for value in vector)

            self._validate_dimension(embedding)

            results.append(
                EmbeddingResult(
                    vector=embedding,
                    model_name=self.config.model_name,
                    dimension=len(embedding),
                )
            )

        return results
    
    def embed_query(
        self,
        query: str,
    ) -> tuple[float, ...]:
        """
        Generate an embedding for a search query.

        Query embeddings use the same configured model and
        normalization settings as repository chunk embeddings.
        """

        if not query.strip():
            raise ValueError("query must not be empty.")

        embedding = self._model.encode(
            query,
            normalize_embeddings=self.config.normalize_embeddings,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        vector = tuple(float(value) for value in embedding)

        self._validate_dimension(vector)

        return vector

    def embed_batch(
        self,
        chunks: Sequence[Chunk],
    ) -> BatchEmbeddingResult:
        """
        Generate embeddings for a batch of chunks and return batch metadata.
        """

        embeddings = self.embed(chunks)

        return BatchEmbeddingResult(
            embeddings=tuple(embeddings),
            model_name=self.config.model_name,
            dimension=self.config.dimension,
            count=len(embeddings),
        )

    def dimension(self) -> int:
        """
        Return the configured embedding dimension.
        """

        return self.config.dimension

    def model_name(self) -> str:
        """
        Return the configured embedding model name.
        """

        return self.config.model_name

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def _load_model(self) -> SentenceTransformer:
        """
        Load the configured embedding model.
        """

        if self.config.provider != EmbeddingProvider.SENTENCE_TRANSFORMERS:
            raise ValueError(
                f"Unsupported embedding provider: " f"{self.config.provider}"
            )

        return SentenceTransformer(self.config.model_name)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_dimension(
        self,
        vector: tuple[float, ...],
    ) -> None:
        """
        Ensure the generated vector matches the configured dimension.
        """

        actual_dimension = len(vector)

        if actual_dimension != self.config.dimension:
            raise ValueError(
                "Embedding dimension mismatch: "
                f"expected {self.config.dimension}, "
                f"got {actual_dimension}."
            )
