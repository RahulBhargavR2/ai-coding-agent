import asyncio
import os
import signal

from app.security.command_policy import (
    CommandPolicy,
    DEFAULT_COMMAND_POLICY,
)
from app.tools.base import Tool, ToolContext, ToolResult
from app.tools.permissions import ToolPermission
from app.schemas.tool import ShellArguments
from app.security.execution_limits import ExecutionLimits, DEFAULT_EXECUTION_LIMITS


class ShellTool(Tool):
    name = "execute_command"
    description = "Execute an allowed command inside the repository."
    arguments_schema = ShellArguments
    permission = ToolPermission.EXECUTE

    def __init__(
        self,
        command_policy: CommandPolicy = DEFAULT_COMMAND_POLICY,
        execution_limits: ExecutionLimits = DEFAULT_EXECUTION_LIMITS,
    ) -> None:
        self.command_policy = command_policy
        self.execution_limits = execution_limits

    async def execute(
        self,
        arguments: dict,
        context: ToolContext,
    ) -> ToolResult:
        if not context.repository_path:
            return ToolResult(
                success=False,
                error="Repository path is required.",
            )

        command = arguments["command"]

        if not self.command_policy.allows(command):
            return ToolResult(
                success=False,
                error=f"Command not allowed: {command[0]}",
            )

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=context.repository_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    asyncio.gather(
                        self._read_stream(
                            process.stdout,
                            self.execution_limits.max_output_bytes,
                        ),
                        self._read_stream(
                            process.stderr,
                            self.execution_limits.max_output_bytes,
                        ),
                    ),
                    timeout=self.execution_limits.timeout_seconds,
                )

            except asyncio.TimeoutError:
                try:
                    os.killpg(
                        process.pid,
                        signal.SIGKILL
                    )
                    await process.wait()
                except ProcessLookupError:
                    pass
                await process.wait()

                return ToolResult(
                    success=False,
                    error=(
                        "Command execution timed out after "
                        f"{self.execution_limits.timeout_seconds} seconds."
                    ),
                )
            stdout_data, stdout_truncated = stdout
            stderr_data, stderr_truncated = stderr

            await process.wait()

            return ToolResult(
                success=process.returncode == 0,
                output={
                    "stdout": stdout_data.decode(errors="replace"),
                    "stderr": stderr_data.decode(errors="replace"),
                    "return_code": process.returncode,
                },
                metadata={
                    "stdout_truncated": stdout_truncated,
                    "stderr_truncated": stderr_truncated,
                },
            )

        except OSError as exc:
            return ToolResult(
                success=False,
                error=str(exc),
            )


    async def _read_stream(
        self,
        stream: asyncio.StreamReader,
        max_bytes: int,
    ) -> tuple[bytes, bool]:
        chunks: list[bytes] = []
        total = 0
        truncated = False

        while True:
            chunk = await stream.read(4096)

            if not chunk:
                break

            remaining = max_bytes - total

            if remaining > 0:
                chunks.append(chunk[:remaining])
                total += min(len(chunk), remaining)

            if len(chunk) > remaining:
                truncated = True

        return b"".join(chunks), truncated
