import pytest

from app.security.sandbox import PathSandbox


def test_resolve_valid_path(tmp_path):
    sandbox = PathSandbox(tmp_path)

    result = sandbox.resolve("app/main.py")

    assert result == tmp_path / "app" / "main.py"


def test_resolve_repository_root(tmp_path):
    sandbox = PathSandbox(tmp_path)

    result = sandbox.resolve(".")

    assert result == tmp_path


def test_reject_path_traversal(tmp_path):
    sandbox = PathSandbox(tmp_path)

    with pytest.raises(PermissionError):
        sandbox.resolve("../../etc/passwd")


def test_reject_absolute_path_outside_repository(tmp_path):
    sandbox = PathSandbox(tmp_path)

    with pytest.raises(PermissionError):
        sandbox.resolve("/etc/passwd")


def test_allow_normalized_relative_path(tmp_path):
    sandbox = PathSandbox(tmp_path)

    result = sandbox.resolve("app/../tests/test.py")

    assert result == tmp_path / "tests" / "test.py"


def test_reject_symlink(tmp_path):
    target = tmp_path / "target.txt"
    target.write_text(
        "secret",
        encoding="utf-8",
    )

    link = tmp_path / "link.txt"

    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("Symlinks are not supported.")

    sandbox = PathSandbox(tmp_path)

    with pytest.raises(PermissionError):
        sandbox.resolve("link.txt")


def test_git_directory_is_ignored(tmp_path):
    sandbox = PathSandbox(tmp_path)

    path = tmp_path / ".git" / "config"

    assert sandbox.is_ignored(path) is True


def test_normal_directory_is_not_ignored(tmp_path):
    sandbox = PathSandbox(tmp_path)

    path = tmp_path / "app" / "main.py"

    assert sandbox.is_ignored(path) is False


def test_reject_oversized_file(tmp_path):
    file_path = tmp_path / "large.txt"

    file_path.write_bytes(b"x" * (5 * 1024 * 1024 + 1))

    sandbox = PathSandbox(tmp_path)

    with pytest.raises(PermissionError):
        sandbox.validate_file_size(file_path)
