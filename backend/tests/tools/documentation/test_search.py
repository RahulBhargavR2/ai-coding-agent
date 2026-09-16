import pytest

from app.tools.base import ToolContext
from app.tools.documentation.search import DocumentationSearchTool


@pytest.mark.asyncio
async def test_documentation_search_finds_markdown_content(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()

    (docs / "README.md").write_text(
        "# Authentication\n" "This project uses JWT authentication.\n",
        encoding="utf-8",
    )

    tool = DocumentationSearchTool()

    context = ToolContext(
        repository_path=str(tmp_path),
    )

    result = await tool.execute(
        arguments={
            "query": "JWT authentication",
        },
        context=context,
    )

    assert result.success is True
    assert len(result.output) == 1

    match = result.output[0]

    assert match["path"] == "docs/README.md"
    assert match["line"] == 2
    assert "JWT authentication" in match["content"]


@pytest.mark.asyncio
async def test_documentation_search_ignores_non_documentation_files(tmp_path):
    (tmp_path / "app.py").write_text(
        "JWT authentication",
        encoding="utf-8",
    )

    (tmp_path / "README.md").write_text(
        "No authentication information here.",
        encoding="utf-8",
    )

    tool = DocumentationSearchTool()

    context = ToolContext(
        repository_path=str(tmp_path),
    )

    result = await tool.execute(
        arguments={
            "query": "JWT authentication",
        },
        context=context,
    )

    assert result.success is True
    assert all(match["path"].endswith((".md", ".mdx")) for match in result.output)
