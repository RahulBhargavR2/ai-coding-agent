from __future__ import annotations

from pathlib import Path


class LanguageDetector:
    """
    Detects the programming or markup language of a repository file.

    Detection is based primarily on file extension. Special filenames
    such as Dockerfile and Makefile are handled explicitly.

    The detector returns canonical language names that can be consumed
    by the parser and chunking layers.
    """

    EXTENSION_LANGUAGE_MAP: dict[str, str] = {
        # Python
        ".py": "python",
        ".pyw": "python",
        ".pyi": "python",
        # JavaScript / TypeScript
        ".js": "javascript",
        ".jsx": "javascript",
        ".mjs": "javascript",
        ".cjs": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".mts": "typescript",
        ".cts": "typescript",
        # JVM
        ".java": "java",
        ".kt": "kotlin",
        ".kts": "kotlin",
        ".scala": "scala",
        ".groovy": "groovy",
        # C / C++
        ".c": "c",
        ".h": "c",
        ".cc": "cpp",
        ".cpp": "cpp",
        ".cxx": "cpp",
        ".hpp": "cpp",
        ".hh": "cpp",
        ".hxx": "cpp",
        # C#
        ".cs": "csharp",
        # Go
        ".go": "go",
        # Rust
        ".rs": "rust",
        # Ruby
        ".rb": "ruby",
        ".rake": "ruby",
        # PHP
        ".php": "php",
        # Swift
        ".swift": "swift",
        # Dart
        ".dart": "dart",
        # Shell
        ".sh": "shell",
        ".bash": "shell",
        ".zsh": "shell",
        ".fish": "shell",
        # SQL
        ".sql": "sql",
        # HTML / CSS
        ".html": "html",
        ".htm": "html",
        ".css": "css",
        ".scss": "scss",
        ".sass": "sass",
        ".less": "less",
        # Data / configuration
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".xml": "xml",
        # Documentation
        ".md": "markdown",
        ".markdown": "markdown",
        ".rst": "restructuredtext",
        ".txt": "text",
        # GraphQL
        ".graphql": "graphql",
        ".gql": "graphql",
        # Lua
        ".lua": "lua",
        # Elixir / Erlang
        ".ex": "elixir",
        ".exs": "elixir",
        ".erl": "erlang",
        ".hrl": "erlang",
        # Haskell
        ".hs": "haskell",
        # R
        ".r": "r",
        # MATLAB
        ".m": "matlab",
        # PowerShell
        ".ps1": "powershell",
        # Protocol / schema files
        ".proto": "protobuf",
        # Terraform
        ".tf": "terraform",
        ".tfvars": "terraform",
        # Docker
        ".dockerfile": "dockerfile",
    }

    FILENAME_LANGUAGE_MAP: dict[str, str] = {
        "Dockerfile": "dockerfile",
        "Containerfile": "dockerfile",
        "Makefile": "makefile",
        "GNUmakefile": "makefile",
        "Jenkinsfile": "groovy",
        "Vagrantfile": "ruby",
        "Gemfile": "ruby",
        "Rakefile": "ruby",
        "Podfile": "ruby",
        "Procfile": "text",
    }

    def detect(
        self,
        file_path: Path,
    ) -> str | None:
        """
        Detect the language for a file.

        Returns:
            Canonical language name, or None when the file type is
            unknown.
        """

        filename = file_path.name

        language = self.FILENAME_LANGUAGE_MAP.get(filename)

        if language is not None:
            return language

        extension = file_path.suffix.lower()

        return self.EXTENSION_LANGUAGE_MAP.get(extension)

    def is_supported(
        self,
        file_path: Path,
    ) -> bool:
        """
        Determine whether a file has a recognized language.
        """

        return self.detect(file_path) is not None
