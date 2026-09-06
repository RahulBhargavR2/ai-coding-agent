from __future__ import annotations

from app.indexing.bm25.bm25_service import BM25Service
from app.indexing.embeddings.embedding_service import EmbeddingService
from app.indexing.vectorstore.qdrant_service import QdrantService
from app.retrieval.models import (
    RetrievedChunk,
    RetrievalQuery,
    RetrievalResult,
)
from app.retrieval.retriever import Retriever
from uuid import UUID


class HybridRetriever(Retriever):
    """
    Combines semantic and lexical repository retrieval.

    Semantic retrieval:
        Qdrant + embeddings

    Lexical retrieval:
        BM25
    """

    def __init__(
        self,
        qdrant_service: QdrantService,
        bm25_service: BM25Service,
        embedding_service: EmbeddingService,
    ) -> None:
        self.qdrant_service = qdrant_service
        self.bm25_service = bm25_service
        self.embedding_service = embedding_service

    def retrieve(
        self,
        query: RetrievalQuery,
    ) -> RetrievalResult:
        """
        Retrieve repository chunks using both semantic and
        lexical search.
        """

        semantic_results = self._semantic_search(query)

        lexical_results = self._lexical_search(query)

        chunks = self._merge_results(
            semantic_results=semantic_results,
            lexical_results=lexical_results,
            limit=query.limit,
        )

        return RetrievalResult(
            query=query.query,
            chunks=chunks,
        )

    # ------------------------------------------------------------------
    # Semantic search
    # ------------------------------------------------------------------

    def _semantic_search(
        self,
        query: RetrievalQuery,
    ):
        """
        Retrieve semantically similar chunks from Qdrant.
        """

        embedding = self.embedding_service.embed_query(query.query)

        return self.qdrant_service.search(
            query_vector=embedding,
            limit=query.limit,
            repository_id=query.repository_id,
        )

    # ------------------------------------------------------------------
    # Lexical search
    # ------------------------------------------------------------------

    def _lexical_search(
        self,
        query: RetrievalQuery,
    ):
        """
        Retrieve lexically matching chunks using BM25.
        """

        return self.bm25_service.search(
            query=query.query,
            limit=query.limit,
            repository_id=query.repository_id,
        )

    # ------------------------------------------------------------------
    # Fusion
    # ------------------------------------------------------------------

    def _merge_results(
        self,
        semantic_results,
        lexical_results,
        limit: int,
    ) -> list[RetrievedChunk]:
        """
        Merge semantic and lexical results.

        For the initial implementation we use normalized score
        fusion. A later retrieval stage can replace this with
        Reciprocal Rank Fusion or cross-encoder reranking.
        """

        merged: dict[str, RetrievedChunk] = {}

        semantic_max = max(
            (float(result.score) for result in semantic_results),
            default=1.0,
        )

        lexical_max = max(
            (float(result.score) for result in lexical_results),
            default=1.0,
        )

        for result in semantic_results:
            normalized_score = (
                float(result.score) / semantic_max if semantic_max > 0 else 0.0
            )

            merged[result.id] = self._to_chunk(
                result=result,
                score=normalized_score,
            )

        for result in lexical_results:
            normalized_score = (
                float(result.score) / lexical_max if lexical_max > 0 else 0.0
            )

            if result.id in merged:
                existing = merged[result.id]

                merged[result.id] = RetrievedChunk(
                    id=existing.id,
                    content=existing.content,
                    score=(existing.score + normalized_score),
                    relative_path=existing.relative_path,
                    language=existing.language,
                    start_line=existing.start_line,
                    end_line=existing.end_line,
                    symbol_name=existing.symbol_name,
                    metadata=existing.metadata,
                )
            else:
                merged[result.id] = self._to_chunk(
                    result=result,
                    score=normalized_score,
                )
        
        return sorted(
            merged.values(),
            key=lambda chunk: chunk.score,
            reverse=True,
        )[:limit]

    # ------------------------------------------------------------------
    # Result conversion
    # ------------------------------------------------------------------

    @staticmethod
    def _to_chunk(
        result,
        score: float,
    ) -> RetrievedChunk:
        payload = result.payload

        return RetrievedChunk(
            id=result.id,
            content=payload.get(
                "content",
                "",
            ),
            score=score,
            relative_path=payload.get(
                "relative_path",
                "",
            ),
            language=payload.get(
                "language",
            ),
            start_line=payload.get(
                "start_line",
            ),
            end_line=payload.get(
                "end_line",
            ),
            symbol_name=payload.get(
                "symbol_name",
            ),
            metadata=payload,
        )
