from app.tools.filesystem.read import ReadFileTool
from app.tools.filesystem.list import ListFilesTool
from app.tools.filesystem.search import SearchFilesTool
from app.tools.git.status import GitStatusTool


def test_read_file_llm_definition():
    tool = ReadFileTool()

    definition = tool.to_llm_definition()

    assert definition["name"] == tool.name
    assert definition["description"] == tool.description

    schema = definition["input_schema"]

    assert schema["type"] == "object"
    assert "path" in schema["properties"]
    assert "path" in schema["required"]


def test_list_files_llm_definition():
    tool = ListFilesTool()

    definition = tool.to_llm_definition()

    assert definition["name"] == tool.name
    assert "path" in definition["input_schema"]["properties"]


def test_search_files_llm_definition():
    tool = SearchFilesTool()

    definition = tool.to_llm_definition()

    schema = definition["input_schema"]

    assert "query" in schema["properties"]
    assert "path" in schema["properties"]
    assert "query" in schema["required"]


def test_git_status_llm_definition():
    tool = GitStatusTool()

    definition = tool.to_llm_definition()

    assert definition["name"] == tool.name
    assert definition["input_schema"]["type"] == "object"
