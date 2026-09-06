from app.indexing.chunking.code_chunker import CodeChunker
from app.indexing.parser.metadata_extractor import MetadataExtractor
from app.indexing.parser.tree_sitter_parser import TreeSitterParser


def test_code_chunker_creates_class_chunk():
    source = """class User:
    def create(self):
        pass
"""

    parser = TreeSitterParser()
    extractor = MetadataExtractor()
    chunker = CodeChunker()

    parsed = parser.parse(
        source_code=source,
        language="python",
    )

    metadata = extractor.extract(parsed)

    chunks = chunker.chunk(
        parsed_source=parsed,
        metadata=metadata,
    )

    assert len(chunks) == 1

    chunk = chunks[0]

    assert chunk.chunk_type == "class"
    assert chunk.language == "python"
    assert chunk.symbol_name == "User"
    assert "class User" in chunk.content


def test_nested_methods_are_not_duplicated_when_class_is_selected():
    source = """class User:
    def create(self):
        pass

    def delete(self):
        pass
"""

    parser = TreeSitterParser()
    extractor = MetadataExtractor()
    chunker = CodeChunker()

    parsed = parser.parse(
        source_code=source,
        language="python",
    )

    metadata = extractor.extract(parsed)

    chunks = chunker.chunk(
        parsed_source=parsed,
        metadata=metadata,
    )

    assert len(chunks) == 1
    assert chunks[0].symbol_name == "User"


def test_function_without_class_creates_function_chunk():
    source = """
    def hello(self):
        return "world"
"""

    parser = TreeSitterParser()
    extractor = MetadataExtractor()
    chunker = CodeChunker()

    parsed = parser.parse(
        source_code=source,
        language="python",
    )


    metadata = extractor.extract(parsed)

    chunks = chunker.chunk(
        parsed_source=parsed,
        metadata=metadata,
    )

    assert len(chunks) == 1
    assert chunks[0].chunk_type == "function"
    assert chunks[0].symbol_name == "hello"


def test_file_without_semantic_constructs_uses_fallback():
    source = """x = 10
y = 20
"""

    parser = TreeSitterParser()
    extractor = MetadataExtractor()
    chunker = CodeChunker()

    parsed = parser.parse(
        source_code=source,
        language="python",
    )

    metadata = extractor.extract(parsed)

    chunks = chunker.chunk(
        parsed_source=parsed,
        metadata=metadata,
    )

    assert len(chunks) == 1

    assert chunks[0].chunk_type == "file"
    assert chunks[0].metadata["fallback"] is True
    assert chunks[0].content == source


def test_empty_source_produces_no_chunks():
    parser = TreeSitterParser()
    extractor = MetadataExtractor()
    chunker = CodeChunker()

    parsed = parser.parse(
        source_code="",
        language="python",
    )

    metadata = extractor.extract(parsed)

    chunks = chunker.chunk(
        parsed_source=parsed,
        metadata=metadata,
    )

    assert chunks == []


def test_large_construct_is_split():
    source = "def large_function():\n" + "\n".join(
        f"    value_{i} = {i}" for i in range(10)
    )

    parser = TreeSitterParser()
    extractor = MetadataExtractor()
    chunker = CodeChunker(max_lines=5)

    parsed = parser.parse(
        source_code=source,
        language="python",
    )

    metadata = extractor.extract(parsed)

    chunks = chunker.chunk(
        parsed_source=parsed,
        metadata=metadata,
    )

    assert len(chunks) > 1

    for chunk in chunks:
        assert chunk.metadata["split_from_large_construct"] is True
        assert chunk.symbol_name == "large_function"
