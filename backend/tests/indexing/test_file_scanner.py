from pathlib import Path
from uuid import uuid4

import pytest

from app.core.exceptions import BusinessValidationError
from app.indexing.scanner.file_scanner import FileScanner
from app.models.enums import RepositoryProvider, RepositoryStatus
from app.models.repository import Repository


@pytest.fixture
def repository(tmp_path):
    return Repository(
        id=uuid4(),
        project_id=uuid4(),
        name="test-repository",
        provider=RepositoryProvider.LOCAL,
        url=None,
        default_branch="main",
        current_branch="main",
        status=RepositoryStatus.PENDING,
        local_path=str(tmp_path),
    )


def test_scan_discovers_python_file(
    repository,
):
    root = Path(repository.local_path)

    (root / "main.py").write_text(
        "print('hello')",
        encoding="utf-8",
    )

    scanner = FileScanner()

    files = scanner.scan(repository)

    assert len(files) == 1

    file = files[0]

    assert file.relative_path == "main.py"
    assert file.file_name == "main.py"
    assert file.extension == ".py"
    assert file.language == "python"
    assert file.size_bytes > 0
    assert file.sha256_hash
    assert file.is_indexed is False


def test_scan_discovers_nested_files(
    repository,
):
    root = Path(repository.local_path)

    (root / "app").mkdir()

    (root / "app" / "main.py").write_text(
        "print('hello')",
        encoding="utf-8",
    )

    (root / "README.md").write_text(
        "# Project",
        encoding="utf-8",
    )

    scanner = FileScanner()

    files = scanner.scan(repository)

    paths = {file.relative_path for file in files}

    assert "app/main.py" in paths
    assert "README.md" in paths


def test_scan_ignores_git_directory(
    repository,
):
    root = Path(repository.local_path)

    (root / ".git").mkdir()

    (root / ".git" / "config").write_text(
        "ignored",
        encoding="utf-8",
    )

    (root / "main.py").write_text(
        "print('hello')",
        encoding="utf-8",
    )

    scanner = FileScanner()

    files = scanner.scan(repository)

    paths = {file.relative_path for file in files}

    assert "main.py" in paths
    assert ".git/config" not in paths


def test_scan_skips_symlink(
    repository,
):
    root = Path(repository.local_path)

    target = root / "main.py"

    target.write_text(
        "print('hello')",
        encoding="utf-8",
    )

    link = root / "link.py"

    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("Symlinks are not supported")

    scanner = FileScanner()

    files = scanner.scan(repository)

    paths = {file.relative_path for file in files}

    assert "main.py" in paths
    assert "link.py" not in paths


def test_sha256_hash_is_deterministic(tmp_path):
    file_path = tmp_path / "test.py"

    file_path.write_text(
        "hello",
        encoding="utf-8",
    )

    first = FileScanner._calculate_sha256(file_path)
    second = FileScanner._calculate_sha256(file_path)

    assert first == second


def test_sha256_hash_changes_when_file_changes(tmp_path):
    file_path = tmp_path / "test.py"

    file_path.write_text(
        "hello",
        encoding="utf-8",
    )

    first = FileScanner._calculate_sha256(file_path)

    file_path.write_text(
        "hello world",
        encoding="utf-8",
    )

    second = FileScanner._calculate_sha256(file_path)

    assert first != second


def test_missing_repository_path_raises():
    repository = Repository(
        id=uuid4(),
        project_id=uuid4(),
        name="test",
        provider=RepositoryProvider.LOCAL,
        local_path=None,
    )

    scanner = FileScanner()

    with pytest.raises(
        BusinessValidationError,
        match="Repository has not been imported yet",
    ):
        scanner.scan(repository)


def test_nonexistent_repository_path_raises():
    repository = Repository(
        id=uuid4(),
        project_id=uuid4(),
        name="test",
        provider=RepositoryProvider.LOCAL,
        local_path="/does/not/exist",
    )

    scanner = FileScanner()

    with pytest.raises(
        BusinessValidationError,
        match="Repository path does not exist",
    ):
        scanner.scan(repository)


def test_repository_path_that_is_file_raises(
    tmp_path,
):
    file_path = tmp_path / "not-a-directory"
    file_path.write_text("hello")

    repository = Repository(
        id=uuid4(),
        project_id=uuid4(),
        name="test",
        provider=RepositoryProvider.LOCAL,
        local_path=str(file_path),
    )

    scanner = FileScanner()

    with pytest.raises(
        BusinessValidationError,
        match="Repository path is not a directory",
    ):
        scanner.scan(repository)


def test_utf8_file_is_read_correctly(
    repository,
):
    root = Path(repository.local_path)

    content = "print('こんにちは')"

    (root / "main.py").write_text(
        content,
        encoding="utf-8",
    )

    scanner = FileScanner()

    files = scanner.scan(repository)

    assert len(files) == 1
    assert files[0].sha256_hash
