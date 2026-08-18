from __future__ import annotations

import re

from app.indexing.chunking.chunker import Chunk


class MarkdownChunker:
    """
    Splits Markdown documents into semantic sections.

    Markdown headings are used as the primary chunk boundaries.
    """

    HEADING_PATTERN = re.compile(r"^(?P<level>#{1,6})\s+(?P<title>.+?)\s*$")

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
        content: str,
        metadata: dict | None = None,
    ) -> list[Chunk]:
        """
        Split Markdown content into heading-based chunks.

        Args:
            content: Markdown document content.
            metadata: Optional metadata associated with the document.

        Returns:
            List of Markdown chunks.
        """

        lines = content.splitlines()

        if not lines:
            return []

        sections = self._build_sections(lines)

        if not sections:
            return [
                self._create_fallback_chunk(
                    content=content,
                    total_lines=len(lines),
                    metadata=metadata,
                )
            ]

        chunks: list[Chunk] = []

        for section in sections:
            chunks.extend(
                self._section_to_chunks(
                    section=section,
                    metadata=metadata,
                )
            )

        return chunks

    # ------------------------------------------------------------------
    # Section parsing
    # ------------------------------------------------------------------

    def _build_sections(
        self,
        lines: list[str],
    ) -> list[dict]:
        """
        Build Markdown sections based on headings.
        """

        sections: list[dict] = []

        current_section: dict | None = None

        for line_number, line in enumerate(
            lines,
            start=1,
        ):
            match = self.HEADING_PATTERN.match(line)

            if match:
                if current_section is not None:
                    current_section["end_line"] = line_number - 1
                    sections.append(current_section)

                current_section = {
                    "level": len(match.group("level")),
                    "title": match.group("title").strip(),
                    "start_line": line_number,
                    "end_line": len(lines),
                    "lines": [line],
                }

                continue

            if current_section is not None:
                current_section["lines"].append(line)

        if current_section is not None:
            sections.append(current_section)

        return sections

    # ------------------------------------------------------------------
    # Section chunks
    # ------------------------------------------------------------------

    def _section_to_chunks(
        self,
        section: dict,
        metadata: dict | None,
    ) -> list[Chunk]:
        """
        Convert a Markdown section into one or more chunks.
        """

        section_lines = section["lines"]

        if not section_lines:
            return []

        content = "\n".join(section_lines)

        if len(section_lines) <= self.max_lines:
            return [
                Chunk(
                    content=content,
                    chunk_type="markdown_section",
                    language="markdown",
                    start_line=section["start_line"],
                    end_line=section["end_line"],
                    symbol_name=section["title"],
                    metadata={
                        **(metadata or {}),
                        "heading_level": section["level"],
                        "heading": section["title"],
                    },
                )
            ]

        return self._split_large_section(
            section=section,
            metadata=metadata,
        )

    def _split_large_section(
        self,
        section: dict,
        metadata: dict | None,
    ) -> list[Chunk]:
        """
        Split a large Markdown section while retaining its heading
        context in each chunk.
        """

        lines = section["lines"]

        heading = lines[0]

        body_lines = lines[1:]

        chunks: list[Chunk] = []

        for index in range(
            0,
            len(body_lines),
            self.max_lines - 1,
        ):
            body_chunk = body_lines[index : index + self.max_lines - 1]

            if not body_chunk:
                continue

            chunk_lines = [
                heading,
                *body_chunk,
            ]

            start_line = section["start_line"] + index

            end_line = start_line + len(body_chunk)

            chunks.append(
                Chunk(
                    content="\n".join(chunk_lines),
                    chunk_type="markdown_section",
                    language="markdown",
                    start_line=start_line,
                    end_line=end_line,
                    symbol_name=section["title"],
                    metadata={
                        **(metadata or {}),
                        "heading_level": section["level"],
                        "heading": section["title"],
                        "split_from_large_section": True,
                    },
                )
            )

        return chunks

    # ------------------------------------------------------------------
    # Fallback
    # ------------------------------------------------------------------

    @staticmethod
    def _create_fallback_chunk(
        content: str,
        total_lines: int,
        metadata: dict | None,
    ) -> Chunk:
        """
        Create a file-level Markdown chunk when the document contains
        no headings.
        """

        return Chunk(
            content=content,
            chunk_type="markdown",
            language="markdown",
            start_line=1,
            end_line=total_lines,
            symbol_name=None,
            metadata={
                **(metadata or {}),
                "fallback": True,
            },
        )
