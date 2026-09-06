from app.indexing.parser.metadata_extractor import MetadataExtractor
from app.indexing.parser.tree_sitter_parser import TreeSitterParser


def test_extract_python_metadata():
    source = """
import os

class UserService:

    def create_user(self):
        pass

def helper():
    pass
"""

    parser = TreeSitterParser()
    extractor = MetadataExtractor()

    parsed = parser.parse(
        source_code=source,
        language="python",
    )

    metadata = extractor.extract(parsed)

    assert metadata.language == "python"

    assert len(metadata.classes) == 1
    assert metadata.classes[0].name == "UserService"

    assert len(metadata.functions) == 1

    function_names = {item.name for item in metadata.functions}

    method_names = {item.name for item in metadata.methods}

    assert "create_user" in method_names
    assert "helper" in function_names

    assert len(metadata.methods) == 1
    assert metadata.methods[0].name == "create_user"

    assert len(metadata.imports) == 1


def test_extract_python_metadata_contains_locations():
    source = """class User:
    def create(self):
        pass
"""

    parser = TreeSitterParser()
    extractor = MetadataExtractor()

    parsed = parser.parse(
        source_code=source,
        language="python",
    )

    metadata = extractor.extract(parsed)

    assert metadata.classes[0].location.start_line == 1
    assert metadata.classes[0].location.end_line == 3

    assert metadata.classes[0].source.startswith("class User")


def test_extract_empty_python_file():
    parser = TreeSitterParser()
    extractor = MetadataExtractor()

    parsed = parser.parse(
        source_code="",
        language="python",
    )

    metadata = extractor.extract(parsed)

    assert metadata.classes == ()
    assert metadata.functions == ()
    assert metadata.methods == ()
    assert metadata.imports == ()
    assert metadata.has_syntax_errors is False


def test_extract_detects_syntax_errors():
    source = """
def broken(
"""

    parser = TreeSitterParser()
    extractor = MetadataExtractor()

    parsed = parser.parse(
        source_code=source,
        language="python",
    )

    metadata = extractor.extract(parsed)

    assert metadata.has_syntax_errors is True


def test_extract_javascript_metadata():
    source = """
import React from "react";

class UserService {
    createUser() {}
}

function helper() {}
"""

    parser = TreeSitterParser()
    extractor = MetadataExtractor()

    parsed = parser.parse(
        source_code=source,
        language="javascript",
    )

    metadata = extractor.extract(parsed)

    assert metadata.language == "javascript"
    assert len(metadata.classes) == 1
    assert metadata.classes[0].name == "UserService"
    assert len(metadata.functions) >= 1
    assert len(metadata.imports) == 1
