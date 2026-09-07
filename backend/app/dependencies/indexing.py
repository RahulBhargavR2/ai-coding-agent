from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated
from fastapi import Depends

from qdrant_client import QdrantClient

from app.core.config import settings
from app.dependencies.uow import UnitOfWorkDep
from app.indexing.bm25.bm25_service import BM25Service
from app.indexing.chunking.code_chunker import CodeChunker
from app.indexing.chunking.markdown_chunker import MarkdownChunker
from app.indexing.embeddings.embedding_service import EmbeddingService
from app.indexing.embeddings.models import (
    EmbeddingConfig,
    EmbeddingProvider,
)
from app.indexing.importers.github_importer import GitHubImporter
from app.indexing.importers.local_importer import LocalImporter
from app.indexing.importers.zip_importer import ZipImporter
from app.indexing.parser.metadata_extractor import MetadataExtractor
from app.indexing.parser.tree_sitter_parser import TreeSitterParser
from app.indexing.scanner.file_scanner import FileScanner
from app.indexing.vectorstore.collections import (
    CollectionNames,
    QdrantCollectionConfig,
)
from app.indexing.vectorstore.qdrant_service import QdrantService
from app.indexing.pipeline import IndexingPipeline
from app.services.workspace.repository_indexing_service import (
    RepositoryIndexingService,
)

from app.retrieval.hybrid_retriever import HybridRetriever

def get_indexing_pipeline(
    uow: UnitOfWorkDep,
) -> IndexingPipeline:
    """
    Build the repository indexing pipeline.
    """

    storage_root = Path(settings.REPOSITORY_STORAGE_PATH)

    github_importer = GitHubImporter(
        storage_root=storage_root,
    )

    zip_importer = ZipImporter(
        storage_root=storage_root,
    )

    local_importer = LocalImporter(
        storage_root=storage_root,
    )

    file_scanner = FileScanner()

    parser = TreeSitterParser()

    metadata_extractor = MetadataExtractor()

    code_chunker = CodeChunker()

    markdown_chunker = MarkdownChunker()

    embedding_service = get_embedding_service()

    qdrant_service = get_qdrant_service(
        embedding_dimension=embedding_service.dimension(),
    )

    bm25_service = BM25Service()

    return IndexingPipeline(
        uow=uow,
        github_importer=github_importer,
        zip_importer=zip_importer,
        local_importer=local_importer,
        file_scanner=file_scanner,
        parser=parser,
        metadata_extractor=metadata_extractor,
        code_chunker=code_chunker,
        markdown_chunker=markdown_chunker,
        embedding_service=embedding_service,
        qdrant_service=qdrant_service,
        bm25_service=bm25_service,
    )


def get_repository_indexing_service(
    uow: UnitOfWorkDep,
) -> RepositoryIndexingService:
    """
    Build the repository indexing application service.
    """

    pipeline = get_indexing_pipeline(
        uow=uow,
    )

    return RepositoryIndexingService(
        uow=uow,
        pipeline=pipeline,
    )


@lru_cache
def get_embedding_service() -> EmbeddingService:
    """
    Create the shared embedding service.

    The model is loaded once and reused by the application process.
    """

    config = EmbeddingConfig(
        provider=EmbeddingProvider.SENTENCE_TRANSFORMERS,
        model_name=settings.EMBEDDING_MODEL_NAME,
        dimension=settings.EMBEDDING_DIMENSION,
        batch_size=settings.EMBEDDING_BATCH_SIZE,
        normalize_embeddings=True,
    )

    return EmbeddingService(
        config=config,
    )


@lru_cache
def get_qdrant_client() -> QdrantClient:
    """
    Create the shared Qdrant client.
    """

    return QdrantClient(
        url=settings.QDRANT_URL,
        # api_key=settings.QDRANT_API_KEY,
    )


def get_qdrant_service(
    embedding_dimension: int = settings.EMBEDDING_DIMENSION,
) -> QdrantService:
    """
    Create the Qdrant service for the configured embedding dimension.
    """

    config = QdrantCollectionConfig(
        name=CollectionNames.CODE,
        vector_dimension=embedding_dimension,
        distance="Cosine",
    )

    return QdrantService(
        client=get_qdrant_client(),
        collection=config,
    )


@lru_cache
def get_bm25_service() -> BM25Service:
    """
    Create the shared BM25 service.

    The BM25 index is maintained in memory and therefore must be
    shared by indexing and retrieval within the application process.
    """

    return BM25Service()


@lru_cache(maxsize=1)
def get_retriever() -> HybridRetriever:
    """
    Create the shared hybrid retriever.
    """

    return HybridRetriever(
        embedding_service=get_embedding_service(),
        qdrant_service=get_qdrant_service(),
        bm25_service=get_bm25_service(),
    )


IndexingPipelineDep = Annotated[
    IndexingPipeline,
    Depends(get_indexing_pipeline)
]

RepositoryIndexingServiceDep = Annotated[
    RepositoryIndexingService,
    Depends(get_repository_indexing_service)
]
