from __future__ import annotations

from enum import Enum
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
    Summary of a repository indexing operation.
    """

    repository_id: UUID

    files_discovered: int

    files_added: int

    files_modified: int

    files_unchanged: int

    files_deleted: int

    files_indexed: int

    chunks_created: int

    embeddings_created: int


class FileChangeType(str, Enum):
    """
    Describes how a filesystem file differs from its indexed state.
    """

    NEW = "new"
    UNCHANGED = "unchanged"
    MODIFIED = "modified"
    DELETED = "deleted"


@dataclass(frozen=True)
class FileChange:
    """
    Represents a detected change to a repository file.
    """

    change_type: FileChangeType
    current: RepositoryFile | None
    previous: RepositoryFile | None


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

            self._set_status(
                repository,
                RepositoryStatus.CLONING,
            )

            self._import_repository(
                repository=repository,
                archive_path=archive_path,
                source_path=source_path,
            )

            self.uow.commit()

            scanned_files = self._scan_repository(
                repository
            )

            changes = self._detect_changes(
                repository=repository,
                scanned_files=scanned_files,
            )

            self._set_status(
                repository,
                RepositoryStatus.INDEXING,
            )

            self.uow.commit()

            self._apply_file_changes(
                repository=repository,
                changes=changes,
            )

            self.uow.commit()

            result = self._index_changes(
                repository=repository,
                changes=changes,
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
            f"Unsupported repository provider: {repository.provider.value}"
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

    def _index_changes(
        self,
        repository: Repository,
        changes: list[FileChange],
    ) -> IndexingResult:
        """
        Index only files that are new or modified.
        """

        files_to_index = [
            change
            for change in changes
            if change.change_type
            in {
                FileChangeType.NEW,
                FileChangeType.MODIFIED,
            }
        ]

        chunks_created = 0
        embeddings_created = 0
        files_indexed = 0

        vector_points: list[VectorPoint] = []
        bm25_documents: list[BM25Document] = []

        # --------------------------------------------------------------
        # Remove stale index data first
        # --------------------------------------------------------------

        for change in changes:
            if change.change_type == FileChangeType.MODIFIED:
                if change.previous is None:
                    continue

                self._remove_file_from_indexes(
                    change.previous
                )

            elif change.change_type == FileChangeType.DELETED:
                if change.previous is None:
                    continue

                self._remove_file_from_indexes(
                    change.previous
                )

        # --------------------------------------------------------------
        # Index new/modified files
        # --------------------------------------------------------------

        for change in files_to_index:
            if change.current is None:
                continue

            chunks = self._process_file(
                repository=repository,
                repository_file=change.current,
            )

            if not chunks:
                change.current.is_indexed = True
                files_indexed += 1
                continue

            embeddings = self.embedding_service.embed(
                chunks
            )

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
                    repository_file=change.current,
                    chunk_index=index,
                )

                payload = self._build_payload(
                    repository=repository,
                    repository_file=change.current,
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

            change.current.is_indexed = True

            files_indexed += 1
            chunks_created += len(chunks)
            embeddings_created += len(embeddings)


        # --------------------------------------------------------------
        # Update vector store
        # --------------------------------------------------------------

        if vector_points:
            self.qdrant_service.upsert(
                vector_points
            )

        # --------------------------------------------------------------
        # Update BM25
        # --------------------------------------------------------------

        if bm25_documents:
            self.bm25_service.add(
                bm25_documents
            )
        
        files_added = sum(
        change.change_type == FileChangeType.NEW
        for change in changes
        )

        files_modified = sum(
            change.change_type == FileChangeType.MODIFIED
            for change in changes
        )

        files_unchanged = sum(
            change.change_type == FileChangeType.UNCHANGED
            for change in changes
        )

        files_deleted = sum(
            change.change_type == FileChangeType.DELETED
            for change in changes
        )

        return IndexingResult(
            repository_id=repository.id,
            files_discovered=(
                files_added
                + files_modified
                + files_unchanged
            ),
            files_added=files_added,
            files_modified=files_modified,
            files_unchanged=files_unchanged,
            files_deleted=files_deleted,
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
    

    def _detect_changes(
        self,
        repository: Repository,
        scanned_files: list[RepositoryFile],
    ) -> list[FileChange]:
        """
        Compare the current filesystem state with the database state.
        """

        existing_files = self.uow.repository_files.list_by_repository(
            repository_id=repository.id,
        )

        existing_by_path = {
            repository_file.relative_path: repository_file
            for repository_file in existing_files
        }

        scanned_by_path = {
            repository_file.relative_path: repository_file
            for repository_file in scanned_files
        }

        changes: list[FileChange] = []

        # --------------------------------------------------------------
        # New and modified files
        # --------------------------------------------------------------

        for relative_path, current_file in scanned_by_path.items():
            previous_file = existing_by_path.get(
                relative_path
            )

            if previous_file is None:
                changes.append(
                    FileChange(
                        change_type=FileChangeType.NEW,
                        current=current_file,
                        previous=None,
                    )
                )

                continue

            if (
                previous_file.sha256_hash
                != current_file.sha256_hash
            ):
                changes.append(
                    FileChange(
                        change_type=FileChangeType.MODIFIED,
                        current=current_file,
                        previous=previous_file,
                    )
                )

                continue

            changes.append(
                FileChange(
                    change_type=FileChangeType.UNCHANGED,
                    current=previous_file,
                    previous=previous_file,
                )
            )

        # --------------------------------------------------------------
        # Deleted files
        # --------------------------------------------------------------

        for relative_path, previous_file in existing_by_path.items():
            if relative_path not in scanned_by_path:
                changes.append(
                    FileChange(
                        change_type=FileChangeType.DELETED,
                        current=None,
                        previous=previous_file,
                    )
                )

        return changes


    def _apply_file_changes(
        self,
        repository: Repository,
        changes: list[FileChange],
    ) -> None:
        """
        Synchronize RepositoryFile database records with the filesystem.
        """

        for change in changes:

            # ----------------------------------------------------------
            # New
            # ----------------------------------------------------------

            if change.change_type == FileChangeType.NEW:
                if change.current is None:
                    continue

                self.uow.repository_files.create(
                    change.current
                )

            # ----------------------------------------------------------
            # Modified
            # ----------------------------------------------------------

            elif change.change_type == FileChangeType.MODIFIED:
                if (
                    change.current is None
                    or change.previous is None
                ):
                    continue

                self._update_repository_file(
                    existing=change.previous,
                    current=change.current,
                )

            # ----------------------------------------------------------
            # Deleted
            # ----------------------------------------------------------

            elif change.change_type == FileChangeType.DELETED:
                if change.previous is None:
                    continue

                self.uow.repository_files.delete(
                    change.previous
                )

            # ----------------------------------------------------------
            # Unchanged
            # ----------------------------------------------------------

            elif change.change_type == FileChangeType.UNCHANGED:
                continue

    
    def _update_repository_file(
        self,
        existing: RepositoryFile,
        current: RepositoryFile,
    ) -> None:
        """
        Update an existing RepositoryFile with newly scanned metadata.
        """

        existing.file_name = current.file_name
        existing.extension = current.extension
        existing.language = current.language
        existing.size_bytes = current.size_bytes
        existing.sha256_hash = current.sha256_hash
        existing.last_modified_at = current.last_modified_at

        existing.is_indexed = False
        existing.is_ignored = False

    
    def _remove_file_from_indexes(
        self,
        repository_file: RepositoryFile,
    ) -> None:
        """
        Remove all indexed representations of a repository file.
        """

        self.qdrant_service.delete_file(
            repository_file_id=repository_file.id,
        )

        self.bm25_service.delete_file(
            repository_file_id=repository_file.id,
        )

    
    def _set_status(
        self,
        repository: Repository,
        status: RepositoryStatus,
    ) -> None:
        """
        Update repository indexing status.
        """

        repository.status = status
