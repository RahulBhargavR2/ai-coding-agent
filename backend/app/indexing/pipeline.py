from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from app.core.exceptions import BusinessValidationError
from app.dependencies.uow import UnitOfWork
from app.indexing.bm25.bm25_service import (
    BM25Document,
    BM25Service,
)
from app.indexing.chunking.code_chunker import CodeChunker
from app.indexing.chunking.markdown_chunker import MarkdownChunker
from app.indexing.embeddings.embedding_service import EmbeddingService
from app.indexing.importers.github_importer import GitHubImporter
from app.indexing.importers.local_importer import LocalImporter
from app.indexing.importers.zip_importer import ZipImporter
from app.indexing.parser.metadata_extractor import MetadataExtractor
from app.indexing.parser.tree_sitter_parser import TreeSitterParser
from app.indexing.scanner.file_scanner import FileScanner
from app.indexing.vectorstore.qdrant_service import (
    QdrantService,
    VectorPoint,
)
from app.models.enums import RepositoryProvider, RepositoryStatus
from app.models.repository import Repository
from app.models.repository_file import RepositoryFile


@dataclass(frozen=True)
class IndexingResult:
    """
    Summary of a completed repository indexing operation.
    """

    repository_id: UUID
    files_discovered: int
    files_indexed: int
    chunks_created: int
    embeddings_created: int


class IndexingPipeline:
    """
    Orchestrates repository import and indexing.

    Pipeline:

        Repository
             ↓
        Importer
             ↓
        FileScanner
             ↓
        RepositoryFile
             ↓
        TreeSitterParser
             ↓
        MetadataExtractor
             ↓
        Chunker
             ↓
        EmbeddingService
             ↓
        Qdrant + BM25

    Database persistence remains handled by UnitOfWork and the
    existing repositories.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        github_importer: GitHubImporter,
        zip_importer: ZipImporter,
        local_importer: LocalImporter,
        file_scanner: FileScanner,
        parser: TreeSitterParser,
        metadata_extractor: MetadataExtractor,
        code_chunker: CodeChunker,
        markdown_chunker: MarkdownChunker,
        embedding_service: EmbeddingService,
        qdrant_service: QdrantService,
        bm25_service: BM25Service,
    ) -> None:
        self.uow = uow

        self.github_importer = github_importer
        self.zip_importer = zip_importer
        self.local_importer = local_importer

        self.file_scanner = file_scanner

        self.parser = parser
        self.metadata_extractor = metadata_extractor

        self.code_chunker = code_chunker
        self.markdown_chunker = markdown_chunker

        self.embedding_service = embedding_service

        self.qdrant_service = qdrant_service
        self.bm25_service = bm25_service

    # ==================================================================
    # Public API
    # ==================================================================

    def run(
        self,
        repository: Repository,
        *,
        archive_path: Path | None = None,
        source_path: Path | None = None,
    ) -> IndexingResult:
        """
        Import and index a repository.

        Args:
            repository:
                Existing Repository database entity.

            archive_path:
                Required for UPLOAD repositories.

            source_path:
                Required for LOCAL repositories.

        Returns:
            IndexingResult containing indexing statistics.
        """

        try:
            self._import_repository(
                repository=repository,
                archive_path=archive_path,
                source_path=source_path,
            )

            self.uow.commit()

            repository_files = self._scan_repository(repository)

            self._persist_repository_files(repository_files)

            self.uow.commit()

            result = self._index_files(
                repository=repository,
                repository_files=repository_files,
            )

            self._mark_repository_ready(repository)

            self.uow.commit()

            return result

        except Exception:
            self._mark_repository_failed(repository)

            self.uow.commit()

            raise

    # ==================================================================
    # Import
    # ==================================================================

    def _import_repository(
        self,
        repository: Repository,
        *,
        archive_path: Path | None,
        source_path: Path | None,
    ) -> None:
        """
        Select the correct importer based on repository provider.
        """

        if repository.provider == RepositoryProvider.GITHUB:
            self.github_importer.import_repository(repository)
            return

        if repository.provider == RepositoryProvider.UPLOAD:
            if archive_path is None:
                raise BusinessValidationError(
                    "archive_path is required for uploaded repositories."
                )

            self.zip_importer.import_repository(
                repository=repository,
                archive_path=archive_path,
            )
            return

        if repository.provider == RepositoryProvider.LOCAL:
            if source_path is None:
                raise BusinessValidationError(
                    "source_path is required for local repositories."
                )

            self.local_importer.import_repository(
                repository=repository,
                source_path=source_path,
            )
            return

        raise BusinessValidationError(
            f"Unsupported repository provider: " f"{repository.provider.value}"
        )

    # ==================================================================
    # Scan
    # ==================================================================

    def _scan_repository(
        self,
        repository: Repository,
    ) -> list[RepositoryFile]:
        """
        Scan the imported repository filesystem.
        """

        return self.file_scanner.scan(repository)

    # ==================================================================
    # RepositoryFile persistence
    # ==================================================================

    def _persist_repository_files(
        self,
        repository_files: list[RepositoryFile],
    ) -> None:
        """
        Persist discovered RepositoryFile entities.
        """

        for repository_file in repository_files:
            self.uow.repository_files.create(repository_file)

    # ==================================================================
    # File indexing
    # ==================================================================

    def _index_files(
        self,
        repository: Repository,
        repository_files: list[RepositoryFile],
    ) -> IndexingResult:
        """
        Parse, chunk, embed and index repository files.
        """

        chunks_created = 0
        embeddings_created = 0
        files_indexed = 0

        bm25_documents: list[BM25Document] = []
        vector_points: list[VectorPoint] = []

        for repository_file in repository_files:
            try:
                chunks = self._process_file(
                    repository=repository,
                    repository_file=repository_file,
                )

                if not chunks:
                    continue

                embeddings = self.embedding_service.embed(chunks)

                if len(embeddings) != len(chunks):
                    raise BusinessValidationError(
                        "Embedding count does not match chunk count."
                    )

                for index, (chunk, embedding) in enumerate(
                    zip(
                        chunks,
                        embeddings,
                        strict=True,
                    )
                ):
                    point_id = self._build_point_id(
                        repository_file=repository_file,
                        chunk_index=index,
                    )

                    payload = self._build_payload(
                        repository=repository,
                        repository_file=repository_file,
                        chunk=chunk,
                    )

                    vector_points.append(
                        VectorPoint(
                            id=point_id,
                            embedding=embedding,
                            payload=payload,
                        )
                    )

                    bm25_documents.append(
                        BM25Document(
                            id=point_id,
                            content=chunk.content,
                            payload=payload,
                        )
                    )

                repository_file.is_indexed = True

                files_indexed += 1
                chunks_created += len(chunks)
                embeddings_created += len(embeddings)

            except Exception:
                repository_file.is_indexed = False
                raise

        if vector_points:
            self.qdrant_service.upsert(vector_points)

        if bm25_documents:
            self.bm25_service.add(bm25_documents)

        return IndexingResult(
            repository_id=repository.id,
            files_discovered=len(repository_files),
            files_indexed=files_indexed,
            chunks_created=chunks_created,
            embeddings_created=embeddings_created,
        )

    # ==================================================================
    # File processing
    # ==================================================================

    def _process_file(
        self,
        repository: Repository,
        repository_file: RepositoryFile,
    ):
        """
        Parse and chunk a single repository file.
        """

        if not repository.local_path:
            raise BusinessValidationError("Repository does not have a local path.")

        file_path = Path(repository.local_path) / repository_file.relative_path

        if not file_path.exists():
            raise BusinessValidationError(
                f"Repository file no longer exists: {file_path}"
            )

        source_code = self._read_file(file_path)

        if repository_file.language == "markdown":
            return self.markdown_chunker.chunk(
                content=source_code,
                metadata={
                    "repository_id": str(repository.id),
                    "repository_file_id": str(repository_file.id),
                    "relative_path": repository_file.relative_path,
                },
            )

        if not repository_file.language:
            return self._create_text_chunk(
                source_code=source_code,
                repository_file=repository_file,
            )

        if not self.parser.is_supported(repository_file.language):
            return self._create_text_chunk(
                source_code=source_code,
                repository_file=repository_file,
            )

        parsed_source = self.parser.parse(
            source_code=source_code,
            language=repository_file.language,
        )

        metadata = self.metadata_extractor.extract(parsed_source)

        return self.code_chunker.chunk(
            parsed_source=parsed_source,
            metadata=metadata,
        )

    # ==================================================================
    # Text fallback
    # ==================================================================

    @staticmethod
    def _create_text_chunk(
        source_code: str,
        repository_file: RepositoryFile,
    ):
        """
        Create a simple file-level chunk for files that do not have
        a supported Tree-sitter grammar.
        """

        from app.indexing.chunking.chunker import Chunk

        if not source_code.strip():
            return []

        return [
            Chunk(
                content=source_code,
                chunk_type="file",
                language=repository_file.language,
                start_line=1,
                end_line=len(source_code.splitlines()),
                symbol_name=None,
                metadata={
                    "repository_file_id": str(repository_file.id),
                    "relative_path": repository_file.relative_path,
                    "fallback": True,
                },
            )
        ]

    # ==================================================================
    # Payload
    # ==================================================================

    @staticmethod
    def _build_payload(
        repository: Repository,
        repository_file: RepositoryFile,
        chunk,
    ) -> dict:
        """
        Build the metadata stored alongside the vector.
        """

        return {
            "repository_id": str(repository.id),
            "repository_file_id": str(repository_file.id),
            "relative_path": repository_file.relative_path,
            "file_name": repository_file.file_name,
            "language": repository_file.language,
            "chunk_type": chunk.chunk_type,
            "symbol_name": chunk.symbol_name,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
            "content": chunk.content,
        }

    # ==================================================================
    # Point identity
    # ==================================================================

    @staticmethod
    def _build_point_id(
        repository_file: RepositoryFile,
        chunk_index: int,
    ) -> str:
        """
        Build a deterministic identifier for a chunk.

        The same repository file + chunk position will therefore map
        to the same Qdrant point during re-indexing.
        """

        return f"{repository_file.id}:" f"{chunk_index}"

    # ==================================================================
    # File reading
    # ==================================================================

    @staticmethod
    def _read_file(
        file_path: Path,
    ) -> str:
        """
        Read a repository file as UTF-8 text.

        Invalid byte sequences are replaced instead of causing the
        entire repository indexing operation to fail.
        """

        return file_path.read_text(
            encoding="utf-8",
            errors="replace",
        )

    # ==================================================================
    # Status handling
    # ==================================================================

    def _mark_repository_ready(
        self,
        repository: Repository,
    ) -> None:
        """
        Mark the repository as successfully indexed.
        """

        repository.status = RepositoryStatus.READY

        from datetime import datetime, timezone

        repository.last_indexed_at = datetime.now(timezone.utc)

    def _mark_repository_failed(
        self,
        repository: Repository,
    ) -> None:
        """
        Mark repository indexing as failed.
        """

        repository.status = RepositoryStatus.FAILED
