from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class ChangeOperation(StrEnum):
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    RENAME = "rename"


class FileChange(BaseModel):
    """
    Represents a single structured change to a repository file.

    The model intentionally contains both the expected/original content
    and the proposed/new content so that changes can later be validated
    before being applied.
    """

    path: str = Field(min_length=1)

    operation: ChangeOperation

    original_content: str | None = None
    new_content: str | None = None

    new_path: str | None = None

    @model_validator(mode="after")
    def validate_change(self) -> "FileChange":
        if self.operation == ChangeOperation.CREATE:
            if self.new_content is None:
                raise ValueError("CREATE operation requires new_content")

            if self.original_content is not None:
                raise ValueError("CREATE operation cannot have original_content")

        elif self.operation == ChangeOperation.MODIFY:
            if self.original_content is None:
                raise ValueError("MODIFY operation requires original_content")

            if self.new_content is None:
                raise ValueError("MODIFY operation requires new_content")

        elif self.operation == ChangeOperation.DELETE:
            if self.original_content is None:
                raise ValueError("DELETE operation requires original_content")

            if self.new_content is not None:
                raise ValueError("DELETE operation cannot have new_content")

        elif self.operation == ChangeOperation.RENAME:
            if self.original_content is None:
                raise ValueError("RENAME operation requires original_content")

            if self.new_content is None:
                raise ValueError("RENAME operation requires new_content")

            if not self.new_path:
                raise ValueError("RENAME operation requires new_path")

        return self
