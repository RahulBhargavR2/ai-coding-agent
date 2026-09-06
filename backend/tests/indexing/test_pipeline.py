from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.core.exceptions import BusinessValidationError
from app.indexing.bm25.bm25_service import BM25Document
from app.indexing.embeddings.models import EmbeddingResult
from app.indexing.pipeline import (
    FileChange,
    FileChangeType,
    IndexingPipeline,
    IndexingResult,
)
from app.indexing.vectorstore.qdrant_service import VectorPoint
from app.models.enums import RepositoryProvider, RepositoryStatus
from app.models.repository import Repository
from app.models.repository_file import RepositoryFile


# ======================================================================
# Fixtures
# ======================================================================


@pytest.fixture
def repository() -> Repository:
    return Repository(
        id=uuid4(),
        project_id=uuid4(),
        name="test-repository",
        provider=RepositoryProvider.GITHUB,
        url="https://github.com/example/test-repository",
        default_branch="main",
        current_branch="main",
        status=RepositoryStatus.PENDING,
    )


@pytest.fixture
def mock_uow():
    repository_files = SimpleNamespace(
        list_by_repository=Mock(),
        create=Mock(),
        delete=Mock(),
    )

    uow = SimpleNamespace(
        repositories=SimpleNamespace(),
        repository_files=repository_files,
        commit=Mock(),
    )

    return uow


@pytest.fixture
def pipeline(mock_uow):
    return IndexingPipeline(
        uow=mock_uow,
        github_importer=SimpleNamespace(import_repository=Mock()),
        zip_importer=SimpleNamespace(import_repository=Mock()),
        local_importer=SimpleNamespace(import_repository=Mock()),
        file_scanner=SimpleNamespace(scan=Mock()),
        parser=SimpleNamespace(
            is_supported=Mock(),
            parse=Mock(),
        ),
        metadata_extractor=SimpleNamespace(extract=Mock()),
        code_chunker=SimpleNamespace(chunk=Mock()),
        markdown_chunker=SimpleNamespace(chunk=Mock()),
        embedding_service=SimpleNamespace(embed=Mock()),
        qdrant_service=SimpleNamespace(
            upsert=Mock(),
            delete_file=Mock(),
        ),
        bm25_service=SimpleNamespace(
            add=Mock(),
            delete_file=Mock(),
        ),
    )


@pytest.fixture
def repository_file(repository) -> RepositoryFile:
    return RepositoryFile(
        id=uuid4(),
        repository_id=repository.id,
        relative_path="app/main.py",
        file_name="main.py",
        extension=".py",
        language="python",
        size_bytes=100,
        sha256_hash="hash",
        is_indexed=False,
    )


def make_chunk(
    content: str = "def hello():\n    return 'world'",
    *,
    chunk_type: str = "function",
    language: str = "python",
    start_line: int = 1,
    end_line: int = 2,
    symbol_name: str | None = "hello",
):
    return SimpleNamespace(
        content=content,
        chunk_type=chunk_type,
        language=language,
        start_line=start_line,
        end_line=end_line,
        symbol_name=symbol_name,
    )


def make_embedding(
    vector: list[float] | None = None,
):
    if vector is None:
        vector = [0.1, 0.2, 0.3]

    return EmbeddingResult(
        vector=vector,
        model_name="",
        dimension=384
    )


# ======================================================================
# _set_status
# ======================================================================


def test_set_status_updates_repository_status(
    pipeline,
    repository,
):
    pipeline._set_status(
        repository,
        RepositoryStatus.INDEXING,
    )

    assert repository.status == RepositoryStatus.INDEXING


# ======================================================================
# _mark_repository_ready
# ======================================================================


def test_mark_repository_ready_sets_status_and_timestamp(
    pipeline,
    repository,
):
    before = datetime.now(timezone.utc)

    pipeline._mark_repository_ready(repository)

    after = datetime.now(timezone.utc)

    assert repository.status == RepositoryStatus.READY
    assert repository.last_indexed_at is not None
    assert before <= repository.last_indexed_at <= after


# ======================================================================
# _mark_repository_failed
# ======================================================================


def test_mark_repository_failed_sets_failed_status(
    pipeline,
    repository,
):
    pipeline._mark_repository_failed(repository)

    assert repository.status == RepositoryStatus.FAILED


# ======================================================================
# _scan_repository
# ======================================================================


def test_scan_repository_delegates_to_file_scanner(
    pipeline,
    repository,
):
    scanned_files = [Mock(spec=RepositoryFile)]

    pipeline.file_scanner.scan.return_value = scanned_files

    result = pipeline._scan_repository(repository)

    assert result == scanned_files

    pipeline.file_scanner.scan.assert_called_once_with(repository)


# ======================================================================
# _persist_repository_files
# ======================================================================


def test_persist_repository_files_creates_each_file(
    pipeline,
):
    files = [
        Mock(spec=RepositoryFile),
        Mock(spec=RepositoryFile),
        Mock(spec=RepositoryFile),
    ]

    pipeline._persist_repository_files(files)

    assert pipeline.uow.repository_files.create.call_count == 3

    pipeline.uow.repository_files.create.assert_any_call(files[0])
    pipeline.uow.repository_files.create.assert_any_call(files[1])
    pipeline.uow.repository_files.create.assert_any_call(files[2])


def test_persist_repository_files_with_empty_list(
    pipeline,
):
    pipeline._persist_repository_files([])

    pipeline.uow.repository_files.create.assert_not_called()


# ======================================================================
# _import_repository
# ======================================================================


def test_github_repository_uses_github_importer(
    pipeline,
    repository,
):
    repository.provider = RepositoryProvider.GITHUB

    pipeline._import_repository(
        repository=repository,
        archive_path=None,
        source_path=None,
    )

    pipeline.github_importer.import_repository.assert_called_once_with(repository)


def test_upload_repository_uses_zip_importer(
    pipeline,
    repository,
    tmp_path,
):
    repository.provider = RepositoryProvider.UPLOAD

    archive_path = tmp_path / "repository.zip"

    pipeline._import_repository(
        repository=repository,
        archive_path=archive_path,
        source_path=None,
    )

    pipeline.zip_importer.import_repository.assert_called_once_with(
        repository=repository,
        archive_path=archive_path,
    )


def test_local_repository_uses_local_importer(
    pipeline,
    repository,
    tmp_path,
):
    repository.provider = RepositoryProvider.LOCAL

    pipeline._import_repository(
        repository=repository,
        archive_path=None,
        source_path=tmp_path,
    )

    pipeline.local_importer.import_repository.assert_called_once_with(
        repository=repository,
        source_path=tmp_path,
    )


def test_upload_repository_requires_archive_path(
    pipeline,
    repository,
):
    repository.provider = RepositoryProvider.UPLOAD

    with pytest.raises(
        BusinessValidationError,
        match="archive_path is required",
    ):
        pipeline._import_repository(
            repository=repository,
            archive_path=None,
            source_path=None,
        )


def test_local_repository_requires_source_path(
    pipeline,
    repository,
):
    repository.provider = RepositoryProvider.LOCAL

    with pytest.raises(
        BusinessValidationError,
        match="source_path is required",
    ):
        pipeline._import_repository(
            repository=repository,
            archive_path=None,
            source_path=None,
        )


def test_unsupported_provider_raises(
    pipeline,
    repository,
):
    repository.provider = SimpleNamespace(value="unsupported")

    with pytest.raises(
        BusinessValidationError,
        match="Unsupported repository provider",
    ):
        pipeline._import_repository(
            repository=repository,
            archive_path=None,
            source_path=None,
        )


# ======================================================================
# _detect_changes
# ======================================================================


def test_detect_changes_identifies_new_modified_unchanged_and_deleted(
    pipeline,
    repository,
):
    existing_file = RepositoryFile(
        id=uuid4(),
        repository_id=repository.id,
        relative_path="app/existing.py",
        file_name="existing.py",
        extension=".py",
        language="python",
        size_bytes=100,
        sha256_hash="same-hash",
        is_indexed=True,
    )

    modified_file = RepositoryFile(
        id=uuid4(),
        repository_id=repository.id,
        relative_path="app/service.py",
        file_name="service.py",
        extension=".py",
        language="python",
        size_bytes=200,
        sha256_hash="old-hash",
        is_indexed=True,
    )

    deleted_file = RepositoryFile(
        id=uuid4(),
        repository_id=repository.id,
        relative_path="app/deleted.py",
        file_name="deleted.py",
        extension=".py",
        language="python",
        size_bytes=50,
        sha256_hash="deleted-hash",
        is_indexed=True,
    )

    unchanged_file = RepositoryFile(
        id=existing_file.id,
        repository_id=repository.id,
        relative_path="app/existing.py",
        file_name="existing.py",
        extension=".py",
        language="python",
        size_bytes=100,
        sha256_hash="same-hash",
        is_indexed=False,
    )

    modified_current = RepositoryFile(
        id=modified_file.id,
        repository_id=repository.id,
        relative_path="app/service.py",
        file_name="service.py",
        extension=".py",
        language="python",
        size_bytes=250,
        sha256_hash="new-hash",
        is_indexed=False,
    )

    new_file = RepositoryFile(
        id=uuid4(),
        repository_id=repository.id,
        relative_path="app/new.py",
        file_name="new.py",
        extension=".py",
        language="python",
        size_bytes=150,
        sha256_hash="new-hash",
        is_indexed=False,
    )

    pipeline.uow.repository_files.list_by_repository.return_value = [
        existing_file,
        modified_file,
        deleted_file,
    ]

    changes = pipeline._detect_changes(
        repository=repository,
        scanned_files=[
            unchanged_file,
            modified_current,
            new_file,
        ],
    )

    changes_by_path = {
        (change.current or change.previous).relative_path: change.change_type
        for change in changes
    }

    assert changes_by_path["app/existing.py"] == (FileChangeType.UNCHANGED)

    assert changes_by_path["app/service.py"] == (FileChangeType.MODIFIED)

    assert changes_by_path["app/new.py"] == (FileChangeType.NEW)

    assert changes_by_path["app/deleted.py"] == (FileChangeType.DELETED)


def test_detect_changes_calls_repository_file_repository(
    pipeline,
    repository,
):
    pipeline.uow.repository_files.list_by_repository.return_value = []

    pipeline._detect_changes(
        repository=repository,
        scanned_files=[],
    )

    pipeline.uow.repository_files.list_by_repository.assert_called_once_with(
        repository_id=repository.id
    )


def test_detect_changes_empty_repository_returns_no_changes(
    pipeline,
    repository,
):
    pipeline.uow.repository_files.list_by_repository.return_value = []

    result = pipeline._detect_changes(
        repository=repository,
        scanned_files=[],
    )

    assert result == []


# ======================================================================
# _update_repository_file
# ======================================================================


def test_update_repository_file_updates_all_scanned_metadata(
    pipeline,
    repository,
):
    existing = RepositoryFile(
        id=uuid4(),
        repository_id=repository.id,
        relative_path="app/main.py",
        file_name="old.py",
        extension=".py",
        language="python",
        size_bytes=100,
        sha256_hash="old-hash",
        is_indexed=True,
        is_ignored=True,
    )

    current = RepositoryFile(
        id=existing.id,
        repository_id=repository.id,
        relative_path="app/main.py",
        file_name="new.py",
        extension=".txt",
        language="text",
        size_bytes=250,
        sha256_hash="new-hash",
        is_indexed=False,
        is_ignored=False,
    )

    modified_at = datetime.now(timezone.utc)
    current.last_modified_at = modified_at

    pipeline._update_repository_file(
        existing=existing,
        current=current,
    )

    assert existing.file_name == "new.py"
    assert existing.extension == ".txt"
    assert existing.language == "text"
    assert existing.size_bytes == 250
    assert existing.sha256_hash == "new-hash"
    assert existing.last_modified_at == modified_at

    assert existing.is_indexed is False
    assert existing.is_ignored is False


# ======================================================================
# _apply_file_changes
# ======================================================================


def test_apply_new_file_creates_repository_file(
    pipeline,
    repository,
    repository_file,
):
    change = FileChange(
        change_type=FileChangeType.NEW,
        current=repository_file,
        previous=None,
    )

    pipeline._apply_file_changes(
        repository=repository,
        changes=[change],
    )

    pipeline.uow.repository_files.create.assert_called_once_with(repository_file)


def test_apply_modified_file_updates_existing_file(
    pipeline,
    repository,
):
    existing = RepositoryFile(
        id=uuid4(),
        repository_id=repository.id,
        relative_path="app/main.py",
        file_name="main.py",
        extension=".py",
        language="python",
        size_bytes=100,
        sha256_hash="old",
        is_indexed=True,
    )

    current = RepositoryFile(
        id=existing.id,
        repository_id=repository.id,
        relative_path="app/main.py",
        file_name="main.py",
        extension=".py",
        language="python",
        size_bytes=200,
        sha256_hash="new",
        is_indexed=False,
    )

    update_mock = Mock()

    pipeline._update_repository_file = update_mock

    change = FileChange(
        change_type=FileChangeType.MODIFIED,
        current=current,
        previous=existing,
    )

    pipeline._apply_file_changes(
        repository=repository,
        changes=[change],
    )

    update_mock.assert_called_once_with(
        existing=existing,
        current=current,
    )


def test_apply_deleted_file_deletes_previous_file(
    pipeline,
    repository,
):
    previous = RepositoryFile(
        id=uuid4(),
        repository_id=repository.id,
        relative_path="app/old.py",
        file_name="old.py",
        extension=".py",
        language="python",
        size_bytes=100,
        sha256_hash="old",
        is_indexed=True,
    )

    change = FileChange(
        change_type=FileChangeType.DELETED,
        current=None,
        previous=previous,
    )

    pipeline._apply_file_changes(
        repository=repository,
        changes=[change],
    )

    pipeline.uow.repository_files.delete.assert_called_once_with(previous)


def test_apply_unchanged_file_does_nothing(
    pipeline,
    repository,
    repository_file,
):
    change = FileChange(
        change_type=FileChangeType.UNCHANGED,
        current=repository_file,
        previous=repository_file,
    )

    pipeline._apply_file_changes(
        repository=repository,
        changes=[change],
    )

    pipeline.uow.repository_files.create.assert_not_called()
    pipeline.uow.repository_files.delete.assert_not_called()


def test_apply_new_file_with_missing_current_does_nothing(
    pipeline,
    repository,
):
    change = FileChange(
        change_type=FileChangeType.NEW,
        current=None,
        previous=None,
    )

    pipeline._apply_file_changes(
        repository=repository,
        changes=[change],
    )

    pipeline.uow.repository_files.create.assert_not_called()


def test_apply_modified_file_with_missing_current_does_nothing(
    pipeline,
    repository,
):
    previous = Mock(spec=RepositoryFile)

    change = FileChange(
        change_type=FileChangeType.MODIFIED,
        current=None,
        previous=previous,
    )

    pipeline._apply_file_changes(
        repository=repository,
        changes=[change],
    )

    pipeline.uow.repository_files.delete.assert_not_called()


def test_apply_modified_file_with_missing_previous_does_nothing(
    pipeline,
    repository,
    repository_file,
):
    change = FileChange(
        change_type=FileChangeType.MODIFIED,
        current=repository_file,
        previous=None,
    )

    pipeline._apply_file_changes(
        repository=repository,
        changes=[change],
    )

    pipeline.uow.repository_files.create.assert_not_called()


def test_apply_deleted_file_with_missing_previous_does_nothing(
    pipeline,
    repository,
):
    change = FileChange(
        change_type=FileChangeType.DELETED,
        current=None,
        previous=None,
    )

    pipeline._apply_file_changes(
        repository=repository,
        changes=[change],
    )

    pipeline.uow.repository_files.delete.assert_not_called()


# ======================================================================
# _remove_file_from_indexes
# ======================================================================


def test_remove_file_from_indexes_removes_from_qdrant_and_bm25(
    pipeline,
    repository_file,
):
    pipeline._remove_file_from_indexes(repository_file)

    pipeline.qdrant_service.delete_file.assert_called_once_with(
        repository_file_id=repository_file.id
    )

    pipeline.bm25_service.delete_file.assert_called_once_with(
        repository_file_id=repository_file.id
    )


# ======================================================================
# _build_point_id
# ======================================================================


def test_point_id_is_deterministic(
    pipeline,
    repository_file,
):
    first = pipeline._build_point_id(
        repository_file,
        0,
    )

    second = pipeline._build_point_id(
        repository_file,
        0,
    )

    assert first == second


def test_different_chunk_indexes_have_different_point_ids(
    pipeline,
    repository_file,
):
    first = pipeline._build_point_id(
        repository_file,
        0,
    )

    second = pipeline._build_point_id(
        repository_file,
        1,
    )

    assert first != second


def test_point_id_contains_file_id_and_chunk_index(
    pipeline,
    repository_file,
):
    result = pipeline._build_point_id(
        repository_file,
        3,
    )

    assert result == f"{repository_file.id}:3"


# ======================================================================
# _build_payload
# ======================================================================


def test_build_payload_contains_chunk_and_file_metadata(
    pipeline,
    repository,
    repository_file,
):
    chunk = make_chunk()

    payload = pipeline._build_payload(
        repository=repository,
        repository_file=repository_file,
        chunk=chunk,
    )

    assert payload == {
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


# ======================================================================
# _read_file
# ======================================================================


def test_read_file_reads_utf8(
    tmp_path,
):
    file_path = tmp_path / "example.py"

    file_path.write_text(
        "def hello():\n    return 'world'\n",
        encoding="utf-8",
    )

    content = IndexingPipeline._read_file(file_path)

    assert content == ("def hello():\n" "    return 'world'\n")


def test_read_file_replaces_invalid_utf8(
    tmp_path,
):
    file_path = tmp_path / "invalid.txt"

    file_path.write_bytes(b"hello \xff world")

    content = IndexingPipeline._read_file(file_path)

    assert "hello" in content
    assert "world" in content
    assert "\ufffd" in content


# ======================================================================
# _create_text_chunk
# ======================================================================


def test_create_text_chunk_returns_file_level_chunk(
    repository_file,
):
    repository_file.language = "text"

    chunks = IndexingPipeline._create_text_chunk(
        source_code="line one\nline two\nline three",
        repository_file=repository_file,
    )

    assert len(chunks) == 1

    chunk = chunks[0]

    assert chunk.content == ("line one\nline two\nline three")
    assert chunk.chunk_type == "file"
    assert chunk.language == "text"
    assert chunk.start_line == 1
    assert chunk.end_line == 3
    assert chunk.symbol_name is None
    assert chunk.metadata["repository_file_id"] == str(repository_file.id)
    assert chunk.metadata["relative_path"] == (repository_file.relative_path)
    assert chunk.metadata["fallback"] is True


def test_create_text_chunk_returns_empty_for_whitespace(
    repository_file,
):
    result = IndexingPipeline._create_text_chunk(
        source_code="   \n\t\n",
        repository_file=repository_file,
    )

    assert result == []


# ======================================================================
# _process_file
# ======================================================================


def test_process_file_raises_when_repository_has_no_local_path(
    pipeline,
    repository,
    repository_file,
):
    repository.local_path = None

    with pytest.raises(
        BusinessValidationError,
        match="does not have a local path",
    ):
        pipeline._process_file(
            repository=repository,
            repository_file=repository_file,
        )


def test_process_file_raises_when_file_does_not_exist(
    pipeline,
    repository,
    repository_file,
    tmp_path,
):
    repository.local_path = str(tmp_path)

    with pytest.raises(
        BusinessValidationError,
        match="no longer exists",
    ):
        pipeline._process_file(
            repository=repository,
            repository_file=repository_file,
        )


def test_process_file_uses_markdown_chunker(
    pipeline,
    repository,
    repository_file,
    tmp_path,
):
    repository.local_path = str(tmp_path)

    repository_file.relative_path = "README.md"
    repository_file.file_name = "README.md"
    repository_file.extension = ".md"
    repository_file.language = "markdown"

    file_path = tmp_path / "README.md"
    file_path.write_text(
        "# Hello\n\nWorld",
        encoding="utf-8",
    )

    chunks = [
        make_chunk(
            content="# Hello\n\nWorld",
            chunk_type="markdown",
            language="markdown",
        )
    ]

    pipeline.markdown_chunker.chunk.return_value = chunks

    result = pipeline._process_file(
        repository=repository,
        repository_file=repository_file,
    )

    assert result == chunks

    pipeline.markdown_chunker.chunk.assert_called_once_with(
        content="# Hello\n\nWorld",
        metadata={
            "repository_id": str(repository.id),
            "repository_file_id": str(repository_file.id),
            "relative_path": repository_file.relative_path,
        },
    )


def test_process_file_uses_text_fallback_when_language_missing(
    pipeline,
    repository,
    repository_file,
    tmp_path,
):
    repository.local_path = str(tmp_path)
    repository_file.language = None
    repository_file.relative_path = "data.txt"

    file_path = tmp_path / "data.txt"
    file_path.write_text(
        "hello\nworld",
        encoding="utf-8",
    )

    result = pipeline._process_file(
        repository=repository,
        repository_file=repository_file,
    )

    assert len(result) == 1
    assert result[0].chunk_type == "file"
    assert result[0].content == "hello\nworld"


def test_process_file_uses_text_fallback_for_unsupported_language(
    pipeline,
    repository,
    repository_file,
    tmp_path,
):
    repository.local_path = str(tmp_path)
    repository_file.language = "unknown"

    file_path = tmp_path / "main.unknown"
    repository_file.relative_path = "main.unknown"

    file_path.write_text(
        "some unsupported source",
        encoding="utf-8",
    )

    pipeline.parser.is_supported.return_value = False

    result = pipeline._process_file(
        repository=repository,
        repository_file=repository_file,
    )

    assert len(result) == 1
    assert result[0].chunk_type == "file"

    pipeline.parser.is_supported.assert_called_once_with("unknown")

    pipeline.parser.parse.assert_not_called()
    pipeline.code_chunker.chunk.assert_not_called()


def test_process_file_uses_parser_metadata_and_code_chunker(
    pipeline,
    repository,
    repository_file,
    tmp_path,
):
    repository.local_path = str(tmp_path)

    file_path = tmp_path / repository_file.relative_path
    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path.write_text(
        "def hello():\n    return 'world'\n",
        encoding="utf-8",
    )

    parsed_source = Mock()
    metadata = Mock()
    chunks = [make_chunk()]

    pipeline.parser.is_supported.return_value = True
    pipeline.parser.parse.return_value = parsed_source
    pipeline.metadata_extractor.extract.return_value = metadata
    pipeline.code_chunker.chunk.return_value = chunks

    result = pipeline._process_file(
        repository=repository,
        repository_file=repository_file,
    )

    assert result == chunks

    pipeline.parser.is_supported.assert_called_once_with(repository_file.language)

    pipeline.parser.parse.assert_called_once_with(
        source_code="def hello():\n    return 'world'\n",
        language=repository_file.language,
    )

    pipeline.metadata_extractor.extract.assert_called_once_with(parsed_source)

    pipeline.code_chunker.chunk.assert_called_once_with(
        parsed_source=parsed_source,
        metadata=metadata,
    )


# ======================================================================
# _index_changes
# ======================================================================


def test_index_changes_indexes_new_file(
    pipeline,
    repository,
    repository_file,
):
    chunk = make_chunk()
    embedding = make_embedding()

    pipeline._process_file = Mock(return_value=[chunk])

    pipeline.embedding_service.embed.return_value = [embedding]

    change = FileChange(
        change_type=FileChangeType.NEW,
        current=repository_file,
        previous=None,
    )

    result = pipeline._index_changes(
        repository=repository,
        changes=[change],
    )

    assert result.repository_id == repository.id
    assert result.files_discovered == 1
    assert result.files_added == 1
    assert result.files_modified == 0
    assert result.files_unchanged == 0
    assert result.files_deleted == 0
    assert result.files_indexed == 1
    assert result.chunks_created == 1
    assert result.embeddings_created == 1

    assert repository_file.is_indexed is True

    pipeline.embedding_service.embed.assert_called_once_with([chunk])

    pipeline.qdrant_service.upsert.assert_called_once()
    pipeline.bm25_service.add.assert_called_once()


def test_index_changes_indexes_modified_file_and_removes_old_indexes(
    pipeline,
    repository,
):
    old_file = RepositoryFile(
        id=uuid4(),
        repository_id=repository.id,
        relative_path="app/main.py",
        file_name="main.py",
        extension=".py",
        language="python",
        size_bytes=100,
        sha256_hash="old",
        is_indexed=True,
    )

    current_file = RepositoryFile(
        id=old_file.id,
        repository_id=repository.id,
        relative_path="app/main.py",
        file_name="main.py",
        extension=".py",
        language="python",
        size_bytes=200,
        sha256_hash="new",
        is_indexed=False,
    )

    chunk = make_chunk()
    embedding = make_embedding()

    pipeline._process_file = Mock(return_value=[chunk])

    pipeline.embedding_service.embed.return_value = [embedding]

    change = FileChange(
        change_type=FileChangeType.MODIFIED,
        current=current_file,
        previous=old_file,
    )

    result = pipeline._index_changes(
        repository=repository,
        changes=[change],
    )

    assert result.files_modified == 1
    assert result.files_indexed == 1
    assert result.chunks_created == 1
    assert result.embeddings_created == 1

    pipeline.qdrant_service.delete_file.assert_called_once_with(
        repository_file_id=old_file.id
    )

    pipeline.bm25_service.delete_file.assert_called_once_with(
        repository_file_id=old_file.id
    )

    pipeline.qdrant_service.upsert.assert_called_once()
    pipeline.bm25_service.add.assert_called_once()


def test_index_changes_removes_deleted_file_from_indexes(
    pipeline,
    repository,
):
    deleted_file = RepositoryFile(
        id=uuid4(),
        repository_id=repository.id,
        relative_path="app/deleted.py",
        file_name="deleted.py",
        extension=".py",
        language="python",
        size_bytes=100,
        sha256_hash="old",
        is_indexed=True,
    )

    change = FileChange(
        change_type=FileChangeType.DELETED,
        current=None,
        previous=deleted_file,
    )

    result = pipeline._index_changes(
        repository=repository,
        changes=[change],
    )

    assert result.files_discovered == 0
    assert result.files_deleted == 1
    assert result.files_indexed == 0
    assert result.chunks_created == 0
    assert result.embeddings_created == 0

    pipeline.qdrant_service.delete_file.assert_called_once_with(
        repository_file_id=deleted_file.id
    )

    pipeline.bm25_service.delete_file.assert_called_once_with(
        repository_file_id=deleted_file.id
    )

    pipeline.embedding_service.embed.assert_not_called()
    pipeline.qdrant_service.upsert.assert_not_called()
    pipeline.bm25_service.add.assert_not_called()


def test_index_changes_does_not_reindex_unchanged_file(
    pipeline,
    repository,
    repository_file,
):
    change = FileChange(
        change_type=FileChangeType.UNCHANGED,
        current=repository_file,
        previous=repository_file,
    )

    result = pipeline._index_changes(
        repository=repository,
        changes=[change],
    )

    assert result.files_discovered == 1
    assert result.files_unchanged == 1
    assert result.files_indexed == 0
    assert result.chunks_created == 0
    assert result.embeddings_created == 0

    (
        pipeline._process_file.assert_not_called()
        if isinstance(
            pipeline._process_file,
            Mock,
        )
        else None
    )

    pipeline.embedding_service.embed.assert_not_called()
    pipeline.qdrant_service.upsert.assert_not_called()
    pipeline.bm25_service.add.assert_not_called()


def test_index_changes_handles_empty_chunks(
    pipeline,
    repository,
    repository_file,
):
    pipeline._process_file = Mock(return_value=[])

    change = FileChange(
        change_type=FileChangeType.NEW,
        current=repository_file,
        previous=None,
    )

    result = pipeline._index_changes(
        repository=repository,
        changes=[change],
    )

    assert result.files_indexed == 1
    assert result.chunks_created == 0
    assert result.embeddings_created == 0

    assert repository_file.is_indexed is True

    pipeline.embedding_service.embed.assert_not_called()
    pipeline.qdrant_service.upsert.assert_not_called()
    pipeline.bm25_service.add.assert_not_called()


def test_index_changes_raises_when_embedding_count_mismatches(
    pipeline,
    repository,
    repository_file,
):
    chunks = [
        make_chunk(content="chunk 1"),
        make_chunk(content="chunk 2"),
    ]

    pipeline._process_file = Mock(return_value=chunks)

    pipeline.embedding_service.embed.return_value = [make_embedding()]

    change = FileChange(
        change_type=FileChangeType.NEW,
        current=repository_file,
        previous=None,
    )

    with pytest.raises(
        BusinessValidationError,
        match="Embedding count does not match chunk count",
    ):
        pipeline._index_changes(
            repository=repository,
            changes=[change],
        )

    pipeline.qdrant_service.upsert.assert_not_called()
    pipeline.bm25_service.add.assert_not_called()


def test_index_changes_skips_missing_current_file(
    pipeline,
    repository,
):
    change = FileChange(
        change_type=FileChangeType.NEW,
        current=None,
        previous=None,
    )

    result = pipeline._index_changes(
        repository=repository,
        changes=[change],
    )

    assert result.files_added == 1
    assert result.files_indexed == 0
    assert result.chunks_created == 0
    assert result.embeddings_created == 0


def test_index_changes_skips_modified_file_with_missing_previous(
    pipeline,
    repository,
    repository_file,
):
    chunk = make_chunk()
    embedding = make_embedding()

    pipeline._process_file = Mock(return_value=[chunk])

    pipeline.embedding_service.embed.return_value = [embedding]

    change = FileChange(
        change_type=FileChangeType.MODIFIED,
        current=repository_file,
        previous=None,
    )

    pipeline._index_changes(
        repository=repository,
        changes=[change],
    )

    pipeline.qdrant_service.delete_file.assert_not_called()
    pipeline.bm25_service.delete_file.assert_not_called()

    pipeline.qdrant_service.upsert.assert_called_once()
    pipeline.bm25_service.add.assert_called_once()


# ======================================================================
# IndexingResult counts
# ======================================================================


def test_index_changes_returns_correct_file_counts(
    pipeline,
    repository,
    repository_file,
):
    new_file = repository_file

    modified_file = RepositoryFile(
        id=uuid4(),
        repository_id=repository.id,
        relative_path="app/service.py",
        file_name="service.py",
        extension=".py",
        language="python",
        size_bytes=100,
        sha256_hash="new",
    )

    unchanged_file = RepositoryFile(
        id=uuid4(),
        repository_id=repository.id,
        relative_path="app/existing.py",
        file_name="existing.py",
        extension=".py",
        language="python",
        size_bytes=100,
        sha256_hash="same",
        is_indexed=True,
    )

    deleted_file = RepositoryFile(
        id=uuid4(),
        repository_id=repository.id,
        relative_path="app/deleted.py",
        file_name="deleted.py",
        extension=".py",
        language="python",
        size_bytes=100,
        sha256_hash="deleted",
        is_indexed=True,
    )

    pipeline._process_file = Mock(return_value=[])

    changes = [
        FileChange(
            change_type=FileChangeType.NEW,
            current=new_file,
            previous=None,
        ),
        FileChange(
            change_type=FileChangeType.MODIFIED,
            current=modified_file,
            previous=Mock(spec=RepositoryFile),
        ),
        FileChange(
            change_type=FileChangeType.UNCHANGED,
            current=unchanged_file,
            previous=unchanged_file,
        ),
        FileChange(
            change_type=FileChangeType.DELETED,
            current=None,
            previous=deleted_file,
        ),
    ]

    result = pipeline._index_changes(
        repository=repository,
        changes=changes,
    )

    assert result.files_discovered == 3
    assert result.files_added == 1
    assert result.files_modified == 1
    assert result.files_unchanged == 1
    assert result.files_deleted == 1
    assert result.files_indexed == 2
    assert result.chunks_created == 0
    assert result.embeddings_created == 0


# ======================================================================
# run()
# ======================================================================


def test_run_successfully_executes_pipeline(
    pipeline,
    repository,
):
    scanned_files = []
    changes = []

    expected_result = IndexingResult(
        repository_id=repository.id,
        files_discovered=0,
        files_added=0,
        files_modified=0,
        files_unchanged=0,
        files_deleted=0,
        files_indexed=0,
        chunks_created=0,
        embeddings_created=0,
    )

    pipeline._import_repository = Mock()
    pipeline._scan_repository = Mock(return_value=scanned_files)
    pipeline._detect_changes = Mock(return_value=changes)
    pipeline._apply_file_changes = Mock()
    pipeline._index_changes = Mock(return_value=expected_result)

    result = pipeline.run(repository)

    assert result == expected_result

    pipeline._import_repository.assert_called_once_with(
        repository=repository,
        archive_path=None,
        source_path=None,
    )

    pipeline._scan_repository.assert_called_once_with(repository)

    pipeline._detect_changes.assert_called_once_with(
        repository=repository,
        scanned_files=scanned_files,
    )

    pipeline._apply_file_changes.assert_called_once_with(
        repository=repository,
        changes=changes,
    )

    pipeline._index_changes.assert_called_once_with(
        repository=repository,
        changes=changes,
    )

    assert repository.status == RepositoryStatus.READY
    assert repository.last_indexed_at is not None

    assert pipeline.uow.commit.call_count == 4


def test_run_sets_cloning_before_import(
    pipeline,
    repository,
):
    call_order = []

    def fake_import(**kwargs):
        call_order.append("import")
        assert repository.status == RepositoryStatus.CLONING

    pipeline._import_repository = Mock(side_effect=fake_import)

    pipeline._scan_repository = Mock(return_value=[])

    pipeline._detect_changes = Mock(return_value=[])

    pipeline._apply_file_changes = Mock()

    pipeline._index_changes = Mock(
        return_value=IndexingResult(
            repository_id=repository.id,
            files_discovered=0,
            files_added=0,
            files_modified=0,
            files_unchanged=0,
            files_deleted=0,
            files_indexed=0,
            chunks_created=0,
            embeddings_created=0,
        )
    )

    pipeline.run(repository)

    assert call_order == ["import"]
    assert repository.status == RepositoryStatus.READY


def test_run_failure_marks_repository_failed(
    pipeline,
    repository,
):
    pipeline._import_repository = Mock(side_effect=RuntimeError("import failed"))

    with pytest.raises(
        RuntimeError,
        match="import failed",
    ):
        pipeline.run(repository)

    assert repository.status == RepositoryStatus.FAILED

    pipeline.uow.commit.assert_called_once()


def test_run_failure_during_scan_marks_repository_failed(
    pipeline,
    repository,
):
    pipeline._import_repository = Mock()

    pipeline._scan_repository = Mock(side_effect=RuntimeError("scan failed"))

    with pytest.raises(
        RuntimeError,
        match="scan failed",
    ):
        pipeline.run(repository)

    assert repository.status == RepositoryStatus.FAILED

    pipeline.uow.commit.assert_called()


def test_run_failure_during_indexing_marks_repository_failed(
    pipeline,
    repository,
):
    pipeline._import_repository = Mock()
    pipeline._scan_repository = Mock(return_value=[])
    pipeline._detect_changes = Mock(return_value=[])
    pipeline._apply_file_changes = Mock()

    pipeline._index_changes = Mock(side_effect=RuntimeError("index failed"))

    with pytest.raises(
        RuntimeError,
        match="index failed",
    ):
        pipeline.run(repository)

    assert repository.status == RepositoryStatus.FAILED

    pipeline.uow.commit.assert_called()


def test_run_passes_archive_path_to_importer(
    pipeline,
    repository,
    tmp_path,
):
    repository.provider = RepositoryProvider.UPLOAD

    archive_path = tmp_path / "repo.zip"

    pipeline._scan_repository = Mock(return_value=[])
    pipeline._detect_changes = Mock(return_value=[])
    pipeline._apply_file_changes = Mock()

    pipeline._index_changes = Mock(
        return_value=IndexingResult(
            repository_id=repository.id,
            files_discovered=0,
            files_added=0,
            files_modified=0,
            files_unchanged=0,
            files_deleted=0,
            files_indexed=0,
            chunks_created=0,
            embeddings_created=0,
        )
    )

    pipeline.run(
        repository,
        archive_path=archive_path,
    )

    pipeline.zip_importer.import_repository.assert_called_once_with(
        repository=repository,
        archive_path=archive_path,
    )


def test_run_passes_source_path_to_importer(
    pipeline,
    repository,
    tmp_path,
):
    repository.provider = RepositoryProvider.LOCAL

    pipeline._scan_repository = Mock(return_value=[])
    pipeline._detect_changes = Mock(return_value=[])
    pipeline._apply_file_changes = Mock()

    pipeline._index_changes = Mock(
        return_value=IndexingResult(
            repository_id=repository.id,
            files_discovered=0,
            files_added=0,
            files_modified=0,
            files_unchanged=0,
            files_deleted=0,
            files_indexed=0,
            chunks_created=0,
            embeddings_created=0,
        )
    )

    pipeline.run(
        repository,
        source_path=tmp_path,
    )

    pipeline.local_importer.import_repository.assert_called_once_with(
        repository=repository,
        source_path=tmp_path,
    )


# ======================================================================
# Complete orchestration / integration-style unit test
# ======================================================================


def test_run_processes_new_file_end_to_end(
    pipeline,
    repository,
    repository_file,
):
    repository.local_path = "/tmp/test-repository"

    chunk = make_chunk()
    embedding = make_embedding()

    pipeline.file_scanner.scan.return_value = [repository_file]

    pipeline.uow.repository_files.list_by_repository.return_value = []

    pipeline._process_file = Mock(return_value=[chunk])

    pipeline.embedding_service.embed.return_value = [embedding]

    result = pipeline.run(repository)

    assert repository.status == RepositoryStatus.READY
    assert repository.last_indexed_at is not None

    assert result.repository_id == repository.id
    assert result.files_discovered == 1
    assert result.files_added == 1
    assert result.files_modified == 0
    assert result.files_unchanged == 0
    assert result.files_deleted == 0
    assert result.files_indexed == 1
    assert result.chunks_created == 1
    assert result.embeddings_created == 1

    pipeline.uow.repository_files.create.assert_called_once_with(repository_file)

    pipeline.qdrant_service.upsert.assert_called_once()
    pipeline.bm25_service.add.assert_called_once()

    assert repository_file.is_indexed is True
