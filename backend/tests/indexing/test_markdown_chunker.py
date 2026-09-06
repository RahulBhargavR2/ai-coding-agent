import pytest

from app.indexing.chunking.markdown_chunker import MarkdownChunker


@pytest.fixture
def chunker():
    return MarkdownChunker()


def test_markdown_sections_are_created(chunker):
    content = """# Introduction

This is introduction.

## Installation

Install the application.

## Usage

Run the application.
"""

    chunks = chunker.chunk(content)

    assert len(chunks) == 3

    assert chunks[0].symbol_name == "Introduction"
    assert chunks[1].symbol_name == "Installation"
    assert chunks[2].symbol_name == "Usage"

    assert chunks[0].chunk_type == "markdown_section"
    assert chunks[0].language == "markdown"


def test_markdown_heading_level_is_preserved(chunker):
    content = """# Introduction

Text.

### Details

More text.
"""

    chunks = chunker.chunk(content)

    assert chunks[0].metadata["heading_level"] == 1
    assert chunks[1].metadata["heading_level"] == 3


def test_markdown_metadata_is_preserved(chunker):
    content = """# Authentication

Login documentation.
"""

    chunks = chunker.chunk(
        content,
        metadata={
            "repository_id": "repo-1",
            "repository_file_id": "file-1",
        },
    )

    assert chunks[0].metadata["repository_id"] == "repo-1"
    assert chunks[0].metadata["repository_file_id"] == "file-1"


def test_markdown_without_headings_uses_fallback(chunker):
    content = """This is a markdown document.

There are no headings.
"""

    chunks = chunker.chunk(content)

    assert len(chunks) == 1

    assert chunks[0].chunk_type == "markdown"
    assert chunks[0].metadata["fallback"] is True
    assert chunks[0].content == content


def test_empty_markdown_returns_empty_list(chunker):
    assert chunker.chunk("") == []


def test_large_markdown_section_is_split():
    chunker = MarkdownChunker(max_lines=5)

    content = "# Large Section\n" + "\n".join(f"Line {i}" for i in range(20))

    chunks = chunker.chunk(content)

    assert len(chunks) > 1

    for chunk in chunks:
        assert chunk.metadata["split_from_large_section"] is True
        assert chunk.symbol_name == "Large Section"
        assert chunk.content.startswith("# Large Section")
