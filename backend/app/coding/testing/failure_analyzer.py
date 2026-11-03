import re

from pydantic import BaseModel, Field

from app.coding.testing.test_result import TestResult


class TestFailure(BaseModel):
    """
    Structured representation of a single test failure.
    """

    test_name: str

    file_path: str | None = None

    line_number: int | None = None

    error_type: str | None = None

    error_message: str | None = None

    traceback: str = ""


class FailureAnalysis(BaseModel):
    """
    Structured analysis of a test execution failure.
    """

    has_failures: bool

    failures: list[TestFailure] = Field(
        default_factory=list,
    )

    summary: str = ""


class FailureAnalyzer:
    """
    Converts normalized test results into structured failure information.
    """

    def analyze(
        self,
        result: TestResult,
    ) -> FailureAnalysis:
        if result.success:
            return FailureAnalysis(
                has_failures=False,
                summary="All tests passed.",
            )

        failures = [
            self._analyze_failure(
                test_name,
                result,
            )
            for test_name in result.failed_tests
        ]

        return FailureAnalysis(
            has_failures=True,
            failures=failures,
            summary=self._build_summary(
                result,
                failures,
            ),
        )

    def _analyze_failure(
        self,
        test_name: str,
        result: TestResult,
    ) -> TestFailure:
        output = f"{result.stdout}\n" f"{result.stderr}"

        file_path, line_number = self._extract_location(
            test_name,
            output,
        )

        error_type, error_message = self._extract_error(output)

        return TestFailure(
            test_name=test_name,
            file_path=file_path,
            line_number=line_number,
            error_type=error_type,
            error_message=error_message,
            traceback=output,
        )

    @staticmethod
    def _extract_location(
        test_name: str,
        output: str,
    ) -> tuple[str | None, int | None]:
        """
        Extract a source location from common pytest output.

        Example:
            tests/test_auth.py:42
        """

        location_match = re.search(
            r"([^\s:]+\.py):(\d+)",
            output,
        )

        if location_match:
            return (
                location_match.group(1),
                int(location_match.group(2)),
            )

        test_match = re.match(
            r"(.+\.py)(?:::|:)",
            test_name,
        )

        if test_match:
            return (
                test_match.group(1),
                None,
            )

        return None, None

    @staticmethod
    def _extract_error(
        output: str,
    ) -> tuple[str | None, str | None]:
        """
        Extract the final Python exception type and message.
        """

        lines = [line.strip() for line in output.splitlines() if line.strip()]

        for line in reversed(lines):
            match = re.match(
                r"([A-Za-z_][A-Za-z0-9_.]*Error)" r"(?:\s*:\s*(.*))?$",
                line,
            )

            if match:
                return (
                    match.group(1),
                    match.group(2) or None,
                )

        return None, None

    @staticmethod
    def _build_summary(
        result: TestResult,
        failures: list[TestFailure],
    ) -> str:
        if not failures:
            return "Tests failed, but no individual " "test failures were identified."

        return f"{len(failures)} test(s) failed. " f"Exit code: {result.exit_code}."
