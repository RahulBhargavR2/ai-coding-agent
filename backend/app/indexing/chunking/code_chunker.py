from __future__ import annotations

from dataclasses import replace

from app.indexing.chunking.chunker import Chunk
from app.indexing.parser.metadata_extractor import CodeMetadata, FileMetadata
from app.indexing.parser.tree_sitter_parser import ParsedSource


class CodeChunker:
    """
    Creates semantic chunks from source-code AST metadata.

    The preferred chunk boundaries are:
    - classes
    - methods
    - functions

    Large constructs are split using a configurable line limit.
    """

    DEFAULT_MAX_LINES = 120

    def __init__(
        self,
        max_lines: int = DEFAULT_MAX_LINES,
    ) -> None:
        if max_lines <= 0:
            raise ValueError("max_lines must be greater than zero.")

        self.max_lines = max_lines

    def chunk(
        self,
        parsed_source: ParsedSource,
        metadata: FileMetadata,
    ) -> list[Chunk]:
        """
        Create semantic chunks from a parsed source file.
        """

        source_lines = parsed_source.source_code.splitlines()

        candidates = (
            list(metadata.classes) + list(metadata.methods) + list(metadata.functions)
        )

        candidates = self._remove_nested_duplicates(candidates)

        chunks: list[Chunk] = []

        for item in sorted(
            candidates,
            key=lambda value: (
                value.location.start_line,
                value.location.end_line,
            ),
        ):
            chunks.extend(
                self._chunk_metadata(
                    item=item,
                    language=parsed_source.language,
                    source_lines=source_lines,
                )
            )

        if not chunks and source_lines:
            chunks.append(
                self._create_fallback_chunk(
                    parsed_source=parsed_source,
                    source_lines=source_lines,
                )
            )

        return chunks

    # ------------------------------------------------------------------
    # Semantic chunks
    # ------------------------------------------------------------------

    def _chunk_metadata(
        self,
        item: CodeMetadata,
        language: str,
        source_lines: list[str],
    ) -> list[Chunk]:
        """
        Convert one semantic AST construct into one or more chunks.
        """

        start_line = item.location.start_line
        end_line = item.location.end_line

        if start_line < 1 or end_line < start_line:
            return []

        content = self._extract_lines(
            source_lines=source_lines,
            start_line=start_line,
            end_line=end_line,
        )

        if not content.strip():
            return []

        if self._line_count(content) <= self.max_lines:
            return [
                Chunk(
                    content=content,
                    chunk_type=self._get_chunk_type(item),
                    language=language,
                    start_line=start_line,
                    end_line=end_line,
                    symbol_name=item.name,
                    metadata={
                        "node_type": item.node_type,
                    },
                )
            ]

        return self._split_large_construct(
            item=item,
            content=content,
            language=language,
        )

    # ------------------------------------------------------------------
    # Large constructs
    # ------------------------------------------------------------------

    def _split_large_construct(
        self,
        item: CodeMetadata,
        content: str,
        language: str,
    ) -> list[Chunk]:
        """
        Split an oversized semantic construct into line-based pieces.

        The semantic identity of the original construct is retained
        in every resulting chunk.
        """

        lines = content.splitlines()

        chunks: list[Chunk] = []

        for index in range(
            0,
            len(lines),
            self.max_lines,
        ):
            chunk_lines = lines[index : index + self.max_lines]

            if not chunk_lines:
                continue

            chunk_start = item.location.start_line + index

            chunk_end = chunk_start + len(chunk_lines) - 1

            chunks.append(
                Chunk(
                    content="\n".join(chunk_lines),
                    chunk_type=self._get_chunk_type(item),
                    language=language,
                    start_line=chunk_start,
                    end_line=chunk_end,
                    symbol_name=item.name,
                    metadata={
                        "node_type": item.node_type,
                        "split_from_large_construct": True,
                    },
                )
            )

        return chunks

    # ------------------------------------------------------------------
    # Fallback
    # ------------------------------------------------------------------

    @staticmethod
    def _create_fallback_chunk(
        parsed_source: ParsedSource,
        source_lines: list[str],
    ) -> Chunk:
        """
        Create a file-level chunk when no semantic constructs were found.
        """

        return Chunk(
            content=parsed_source.source_code,
            chunk_type="file",
            language=parsed_source.language,
            start_line=1,
            end_line=len(source_lines),
            symbol_name=None,
            metadata={
                "fallback": True,
            },
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_lines(
        source_lines: list[str],
        start_line: int,
        end_line: int,
    ) -> str:
        """
        Extract a one-based inclusive line range.
        """

        return "\n".join(source_lines[start_line - 1 : end_line])

    @staticmethod
    def _line_count(
        content: str,
    ) -> int:
        """
        Return the number of lines in a chunk.
        """

        return len(content.splitlines())

    @staticmethod
    def _get_chunk_type(
        metadata: CodeMetadata,
    ) -> str:
        """
        Map AST metadata to an application-level chunk type.
        """

        node_type = metadata.node_type

        if "class" in node_type:
            return "class"

        if "method" in node_type or metadata.name is not None:
            return "function"

        return "code"

    @staticmethod
    def _remove_nested_duplicates(
        candidates: list[CodeMetadata],
    ) -> list[CodeMetadata]:
        """
        Remove semantic constructs that are completely contained
        inside another candidate construct.

        This prevents a class and all of its methods from producing
        overlapping chunks when the class itself is selected as a
        semantic unit.
        """

        ordered = sorted(
            candidates,
            key=lambda item: (
                item.location.start_line,
                -item.location.end_line,
            ),
        )

        result: list[CodeMetadata] = []

        for candidate in ordered:
            candidate_start = candidate.location.start_line
            candidate_end = candidate.location.end_line

            is_nested = False

            for existing in result:
                existing_start = existing.location.start_line
                existing_end = existing.location.end_line

                if (
                    existing_start <= candidate_start
                    and existing_end >= candidate_end
                    and (
                        existing_start != candidate_start
                        or existing_end != candidate_end
                    )
                ):
                    is_nested = True
                    break

            if not is_nested:
                result.append(candidate)

        return result
