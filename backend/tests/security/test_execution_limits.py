from app.security.execution_limits import (
    DEFAULT_EXECUTION_LIMITS,
    ExecutionLimits,
)


def test_execution_limits_have_safe_defaults():
    limits = DEFAULT_EXECUTION_LIMITS

    assert limits.timeout_seconds == 30.0
    assert limits.max_output_bytes == 1_000_000


def test_execution_limits_are_configurable():
    limits = ExecutionLimits(
        timeout_seconds=10.0,
        max_output_bytes=500_000,
    )

    assert limits.timeout_seconds == 10.0
    assert limits.max_output_bytes == 500_000


