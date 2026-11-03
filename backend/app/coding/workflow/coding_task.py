from enum import StrEnum

from pydantic import BaseModel, Field


class CodingTaskStatus(StrEnum):
    PENDING = "pending"
    PLANNING = "planning"
    RETRIEVING = "retrieving"
    CODING = "coding"
    REVIEWING = "reviewing"
    APPLYING = "applying"
    TESTING = "testing"
    ANALYZING_FAILURE = "analyzing_failure"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class CodingTask(BaseModel):
    """
    Runtime state of an autonomous coding task.
    """

    task_id: str

    repository_id: str

    instruction: str = Field(
        min_length=1,
    )

    status: CodingTaskStatus = CodingTaskStatus.PENDING

    iteration: int = 0

    max_iterations: int = Field(
        default=3,
        ge=1,
    )

    tests_passed: bool = False

    error: str | None = None

    @property
    def can_retry(self) -> bool:
        return self.iteration < self.max_iterations
