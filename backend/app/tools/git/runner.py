import asyncio
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GitResult:
    success: bool
    stdout: str = ""
    stderr: str = ""
    return_code: int = 0


class GitRunner:
    def __init__(
        self,
        repository_path: str | Path,
        timeout: float = 30.0,
    ) -> None:
        self.repository_path = Path(repository_path).resolve()

        if not self.repository_path.exists():
            raise ValueError("Repository path does not exist.")

        if not self.repository_path.is_dir():
            raise ValueError("Repository path is not a directory.")

        self.timeout = timeout

    async def run(
        self,
        *arguments: str,
    ) -> GitResult:
        command = ["git", *arguments]

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=self.repository_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout,
            )

        except asyncio.TimeoutError:
            try:
                process.kill()
            except ProcessLookupError:
                pass

            await process.communicate()

            return GitResult(
                success=False,
                stdout="",
                stderr="Git command timed out",
                return_code=-1,
            )
        except OSError as exc:
            return GitResult(
                success=False,
                stderr=str(exc),
                return_code=-1,
            )

        stdout_text = stdout.decode("utf-8", errors="replace")
        stderr_text = stderr.decode("utf-8", errors="replace")

        return GitResult(
            success=process.returncode == 0,
            stdout=stdout_text,
            stderr=stderr_text,
            return_code=process.returncode,
        )
