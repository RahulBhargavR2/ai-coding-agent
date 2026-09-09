from dataclasses import dataclass
from typing import Any
from abc import ABC, abstractmethod

from pydantic import BaseModel

@dataclass
class ToolResult:
    success: bool
    output: Any = None
    error: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class ToolContext:
    workspace_id: str | None = None
    repository_id: str | None = None
    repository_path: str | None = None


class Tool(ABC):
    name: str
    description: str
    arguments_schema: type[BaseModel]

    @abstractmethod
    async def execute(
        self, arguments: dict[str, Any], context: ToolContext
    ) -> ToolResult:
        """
        Execute the tool
        """

        raise NotImplementedError
