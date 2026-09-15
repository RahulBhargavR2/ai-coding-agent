from pydantic import BaseModel, ConfigDict, Field


class ToolArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReadFileArguments(ToolArguments):
    path: str = Field(min_length=1)


class ListFilesArguments(ToolArguments):
    path: str = Field(default=".", min_length=1)


class SearchFilesArguments(ToolArguments):
    query: str = Field(min_length=1)
    path: str = Field(default=".", min_length=1)


class EmptyToolArguments(ToolArguments):
    pass

class WriteFileArguments(ToolArguments):
    path: str = Field(min_length=1)
    content: str
