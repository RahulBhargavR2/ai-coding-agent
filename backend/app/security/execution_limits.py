from dataclasses import dataclass

@dataclass(frozen=True)
class ExecutionLimits:
    timeout_seconds: float = 30.0
    max_output_bytes: int = 1_000_000

DEFAULT_EXECUTION_LIMITS = ExecutionLimits()
