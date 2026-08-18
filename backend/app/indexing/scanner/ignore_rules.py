from __future__ import annotations

from pathlib import Path


class IgnoreRules:
    """
    Defines rules for excluding files and directories from
    repository indexing.

    The rules are intentionally independent from the file scanner
    so that scanning and ignore decisions remain separate concerns.
    """

    DEFAULT_IGNORED_DIRECTORIES: frozenset[str] = frozenset(
        {
            ".git",
            ".hg",
            ".svn",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            ".tox",
            ".nox",
            ".venv",
            "venv",
            "env",
            "node_modules",
            "bower_components",
            "dist",
            "build",
            "target",
            "out",
            "coverage",
            ".coverage",
            ".next",
            ".nuxt",
            ".turbo",
            ".cache",
            ".idea",
            ".vscode",
        }
    )

    DEFAULT_IGNORED_EXTENSIONS: frozenset[str] = frozenset(
        {
            # Images
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".webp",
            ".bmp",
            ".ico",
            ".tiff",
            ".svg",
            # Audio / video
            ".mp3",
            ".wav",
            ".ogg",
            ".mp4",
            ".avi",
            ".mov",
            ".mkv",
            ".webm",
            # Archives
            ".zip",
            ".tar",
            ".gz",
            ".bz2",
            ".xz",
            ".7z",
            ".rar",
            # Executables / binaries
            ".exe",
            ".dll",
            ".so",
            ".dylib",
            ".bin",
            ".class",
            ".pyc",
            ".pyo",
            # Object files
            ".o",
            ".obj",
            # Database files
            ".db",
            ".sqlite",
            ".sqlite3",
            # Build artifacts
            ".wasm",
        }
    )

    DEFAULT_IGNORED_FILES: frozenset[str] = frozenset(
        {
            ".DS_Store",
            "Thumbs.db",
            "desktop.ini",
        }
    )

    def __init__(
        self,
        ignored_directories: frozenset[str] | None = None,
        ignored_extensions: frozenset[str] | None = None,
        ignored_files: frozenset[str] | None = None,
    ) -> None:
        """
        Initialize ignore rules.

        Custom rules replace the corresponding defaults when supplied.
        """

        self.ignored_directories = (
            ignored_directories
            if ignored_directories is not None
            else self.DEFAULT_IGNORED_DIRECTORIES
        )

        self.ignored_extensions = (
            ignored_extensions
            if ignored_extensions is not None
            else self.DEFAULT_IGNORED_EXTENSIONS
        )

        self.ignored_files = (
            ignored_files if ignored_files is not None else self.DEFAULT_IGNORED_FILES
        )

    # ------------------------------------------------------------------
    # Directory rules
    # ------------------------------------------------------------------

    def should_ignore_directory(
        self,
        directory: Path,
    ) -> bool:
        """
        Determine whether a directory should be excluded.
        """

        return directory.name in self.ignored_directories

    # ------------------------------------------------------------------
    # File rules
    # ------------------------------------------------------------------

    def should_ignore_file(
        self,
        file_path: Path,
    ) -> bool:
        """
        Determine whether a file should be excluded.
        """

        if file_path.name in self.ignored_files:
            return True

        extension = file_path.suffix.lower()

        return extension in self.ignored_extensions

    # ------------------------------------------------------------------
    # Generic path rule
    # ------------------------------------------------------------------

    def should_ignore(
        self,
        path: Path,
    ) -> bool:
        """
        Determine whether a filesystem path should be ignored.
        """

        if path.is_dir():
            return self.should_ignore_directory(path)

        if path.is_file():
            return self.should_ignore_file(path)

        return True
