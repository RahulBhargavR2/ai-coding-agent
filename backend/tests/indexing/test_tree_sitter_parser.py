import pytest

from app.indexing.parser.tree_sitter_parser import TreeSitterParser


@pytest.fixture
def parser():
    return TreeSitterParser()


def test_parse_python_source(parser):
    source = """
def hello():
    return "world"
"""

    result = parser.parse(
        source_code=source,
        language="python",
    )

    assert result.language == "python"
    assert result.source_code == source
    assert result.tree is not None
    assert result.tree.root_node.type == "module"


def test_parse_javascript_source(parser):
    source = """
function hello() {
    return "world";
}
"""

    result = parser.parse(
        source_code=source,
        language="javascript",
    )

    assert result.language == "javascript"
    assert result.tree is not None


def test_is_supported_returns_true_for_supported_language(parser):
    assert parser.is_supported("python") is True
    assert parser.is_supported("javascript") is True


def test_is_supported_is_case_insensitive(parser):
    assert parser.is_supported("Python") is True
    assert parser.is_supported("PYTHON") is True


def test_is_supported_returns_false_for_unknown_language(parser):
    assert parser.is_supported("unknown") is False


def test_parse_unsupported_language_raises(parser):
    with pytest.raises(
        ValueError,
        match="Unsupported Tree-sitter language",
    ):
        parser.parse(
            source_code="hello",
            language="unknown",
        )


def test_supported_languages_returns_registered_languages(parser):
    languages = parser.supported_languages()

    assert "python" in languages
    assert "javascript" in languages
    assert "typescript" in languages
    assert "java" in languages
    assert "rust" in languages


def test_supported_languages_are_sorted(parser):
    languages = parser.supported_languages()

    assert languages == tuple(sorted(languages))
