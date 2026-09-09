from pathlib import Path


DEFAULT_IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
}

MAX_READ_FILE_SIZE = 5 * 1024 * 1024

class PathSandbox:
    """
    Restricts filesystem access to a repository root.
    """

    def __init__(self, repository_path: str | Path) -> None:
        self.repository_path = Path(repository_path).resolve()

    def resolve(self, path: str | Path) -> Path:
        """
        Resolve a repository-relative path and ensure it remains
        inside the repository root.
        """

        candidate = self.repository_path / path

        if candidate.is_symlink():
            raise PermissionError("Symlink paths are not allowed")

        candidate = candidate.resolve()

        try:
            candidate.relative_to(self.repository_path)
        except ValueError:
            raise PermissionError("Path is outside the repository sandbox.")

        return candidate

    def is_ignored(self, path: Path) -> bool:
        return any(
            part in DEFAULT_IGNORED_DIRECTORIES
            for part in path.parts
        )

    def validate_file_size(self, path: Path) -> None:
        if path.stat().st_size > MAX_READ_FILE_SIZE:
            raise PermissionError(
                "File exceeds the maximum allowed size."
            )