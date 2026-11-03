import re
import time

from app.coding.testing.test_result import TestResult
from app.tools.base import ToolContext
from app.tools.tool_service import ToolService


class TestRunner:
    """
    Executes a test command through the existing tool infrastructure
    and normalizes the result into TestResult.
    """

    def __init__(
        self,
        tool_service: ToolService | None = None,
    ) -> None:
        self.tool_service = tool_service or ToolService()

    async def run(
        self,
        command: list[str],
        context: ToolContext,
    ) -> TestResult:
        """
        Execute a test command through the shell tool.
        """

        start = time.perf_counter()

        result = await self.tool_service.execute(
            tool_name="execute_command",
            arguments={
                "command": command,
            },
            context=context,
        )

        duration_ms = int((time.perf_counter() - start) * 1000)

        if not result.success:
            return TestResult(
                success=False,
                exit_code=self._extract_exit_code(result),
                duration_ms=duration_ms,
                stdout=self._extract_stdout(result),
                stderr=self._extract_stderr(result, result.error),
                failed_tests=self._extract_failed_tests(
                    self._extract_stdout(result),
                    self._extract_stderr(result, result.error),
                ),
            )

        stdout = self._extract_stdout(result)
        stderr = self._extract_stderr(result)

        failed_tests = self._extract_failed_tests(
            stdout,
            stderr,
        )

        total_tests, passed_tests, skipped_tests = self._extract_test_counts(stdout)

        return TestResult(
            success=True,
            exit_code=self._extract_exit_code(result),
            duration_ms=duration_ms,
            stdout=stdout,
            stderr=stderr,
            failed_tests=failed_tests,
            total_tests=total_tests,
            passed_tests=passed_tests,
            skipped_tests=skipped_tests,
        )

    @staticmethod
    def _extract_stdout(result) -> str:
        if not isinstance(result.output, dict):
            return ""

        return result.output.get(
            "stdout",
            "",
        )

    @staticmethod
    def _extract_stderr(
        result,
        fallback: str | None = None,
    ) -> str:
        if not isinstance(result.output, dict):
            return fallback or ""

        return result.output.get(
            "stderr",
            fallback or "",
        )

    @staticmethod
    def _extract_exit_code(result) -> int:
        if isinstance(result.output, dict):
            return result.output.get(
                "return_code",
                1,
            )

        return 1

    @staticmethod
    def _extract_failed_tests(
        stdout: str,
        stderr: str,
    ) -> list[str]:
        output = f"{stdout}\n{stderr}"

        failed: list[str] = []

        for line in output.splitlines():
            match = re.match(
                r"FAILED\s+(.+)",
                line.strip(),
            )

            if match:
                failed.append(match.group(1).strip())

        return failed

    @staticmethod
    def _extract_test_counts(
        stdout: str,
    ) -> tuple[int | None, int | None, int | None]:
        """
        Parse common pytest summary output.

        Example:
            5 passed, 2 failed, 1 skipped
        """

        passed_match = re.search(
            r"(\d+)\s+passed",
            stdout,
        )

        failed_match = re.search(
            r"(\d+)\s+failed",
            stdout,
        )

        skipped_match = re.search(
            r"(\d+)\s+skipped",
            stdout,
        )

        passed = (
            int(passed_match.group(1))
            if passed_match
            else 0
        )

        failed = (
            int(failed_match.group(1))
            if failed_match
            else 0
        )

        skipped = (
            int(skipped_match.group(1))
            if skipped_match
            else 0
        )

        if not passed_match and not failed_match and not skipped_match:
            return None, None, None

        total = passed + failed + skipped

        return total, passed, skipped