from pydantic import BaseModel, Field, model_validator

from app.coding.changes.change import FileChange


class Patch(BaseModel):
    """
    Represents a complete set of file changes produced by the coding agent.
    """

    changes: list[FileChange] = Field(default_factory=list)

    description: str = ""

    @model_validator(mode="after")
    def validate_patch(self) -> "Patch":
        paths: set[str] = set()

        for change in self.changes:
            if change.path in paths:
                raise ValueError(f"Duplicate change path: {change.path}")

            paths.add(change.path)

        return self

    @property
    def is_empty(self) -> bool:
        return len(self.changes) == 0

    @property
    def files_changed(self) -> int:
        return len(self.changes)
