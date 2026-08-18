from __future__ import annotations

from dataclasses import dataclass

from tree_sitter import Language, Parser, Tree

import tree_sitter_c
import tree_sitter_cpp
import tree_sitter_c_sharp
import tree_sitter_go
import tree_sitter_java
import tree_sitter_javascript
import tree_sitter_kotlin
import tree_sitter_php
import tree_sitter_python
import tree_sitter_ruby
import tree_sitter_rust
import tree_sitter_swift
import tree_sitter_typescript


@dataclass(frozen=True)
class ParsedSource:
    """
    Represents the parsed representation of a source file.
    """

    language: str
    source_code: str
    tree: Tree


class TreeSitterParser:
    """
    Parses supported source files using Tree-sitter.

    Responsibilities:
    - Maintain the language-to-grammar registry.
    - Create Tree-sitter parsers.
    - Parse source code.
    - Return syntax trees.

    This class does not:
    - Extract semantic metadata.
    - Create chunks.
    - Generate embeddings.
    - Persist ASTs.
    """

    def __init__(self) -> None:
        self._languages = self._build_language_registry()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(
        self,
        source_code: str,
        language: str,
    ) -> ParsedSource:
        """
        Parse source code using the grammar associated with a language.

        Args:
            source_code: Source code to parse.
            language: Canonical language name.

        Returns:
            ParsedSource containing the syntax tree.

        Raises:
            ValueError:
                If the language is not supported.
        """

        tree_sitter_language = self._get_language(language)

        parser = Parser()
        parser.language = tree_sitter_language

        source_bytes = source_code.encode("utf-8")

        tree = parser.parse(source_bytes)

        return ParsedSource(
            language=language,
            source_code=source_code,
            tree=tree,
        )

    def is_supported(
        self,
        language: str,
    ) -> bool:
        """
        Determine whether a language has a registered Tree-sitter grammar.
        """

        return language.lower() in self._languages

    def supported_languages(self) -> tuple[str, ...]:
        """
        Return all supported canonical language names.
        """

        return tuple(sorted(self._languages.keys()))

    # ------------------------------------------------------------------
    # Language registry
    # ------------------------------------------------------------------

    @staticmethod
    def _build_language_registry() -> dict[str, Language]:
        """
        Build the canonical language-to-Tree-sitter grammar registry.
        """

        return {
            "python": Language(tree_sitter_python.language()),
            "javascript": Language(tree_sitter_javascript.language()),
            "typescript": Language(tree_sitter_typescript.language_typescript()),
            "tsx": Language(tree_sitter_typescript.language_tsx()),
            "java": Language(tree_sitter_java.language()),
            "c": Language(tree_sitter_c.language()),
            "cpp": Language(tree_sitter_cpp.language()),
            "csharp": Language(tree_sitter_c_sharp.language()),
            "go": Language(tree_sitter_go.language()),
            "rust": Language(tree_sitter_rust.language()),
            "ruby": Language(tree_sitter_ruby.language()),
            "php": Language(tree_sitter_php.language_php()),
            "kotlin": Language(tree_sitter_kotlin.language()),
            "swift": Language(tree_sitter_swift.language()),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_language(
        self,
        language: str,
    ) -> Language:
        """
        Retrieve a Tree-sitter grammar for a canonical language name.
        """

        normalized_language = language.lower()

        tree_sitter_language = self._languages.get(normalized_language)

        if tree_sitter_language is None:
            raise ValueError(f"Unsupported Tree-sitter language: {language}")

        return tree_sitter_language
