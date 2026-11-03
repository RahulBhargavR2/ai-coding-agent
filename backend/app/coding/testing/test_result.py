from pydantic import BaseModel, Field


class TestResult(BaseModel):
    """
    Normalized result of a test execution.
    """

    success: bool

    exit_code: int

    duration_ms: int = Field(
        ge=0,
    )

    stdout: str = ""

    stderr: str = ""

    failed_tests: list[str] = Field(
        default_factory=list,
    )

    total_tests: int | None = Field(
        default=None,
        ge=0,
    )

    passed_tests: int | None = Field(
        default=None,
        ge=0,
    )

    skipped_tests: int | None = Field(
        default=None,
        ge=0,
    )

    @property
    def has_failures(self) -> bool:
        return not self.success

    @property
    def failure_count(self) -> int:
        return len(self.failed_tests)
