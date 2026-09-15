from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from pydantic import BaseModel

from app.tools.permissions import ToolPermission

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
    allowed_permissions: set[ToolPermission] | None = None


class Tool(ABC):
    name: str
    description: str
    arguments_schema: type[BaseModel]

    def to_llm_definition(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.arguments_schema.model_json_schema(),
        }

    @abstractmethod
    async def execute(
        self,
        arguments: dict[str, Any],
        context: ToolContext,
    ) -> ToolResult:
        raise NotImplementedError
