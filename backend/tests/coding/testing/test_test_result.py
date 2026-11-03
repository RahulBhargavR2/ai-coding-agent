import pytest
from pydantic import ValidationError

from app.coding.testing.test_result import TestResult


def test_successful_test_result():
    result = TestResult(
        success=True,
        exit_code=0,
        duration_ms=1250,
        stdout="25 passed\n",
        stderr="",
        total_tests=25,
        passed_tests=25,
        skipped_tests=0,
    )

    assert result.success is True
    assert result.exit_code == 0
    assert result.duration_ms == 1250

    assert result.total_tests == 25
    assert result.passed_tests == 25
    assert result.skipped_tests == 0

    assert result.failed_tests == []

    assert result.has_failures is False
    assert result.failure_count == 0


def test_failed_test_result():
    result = TestResult(
        success=False,
        exit_code=1,
        duration_ms=2300,
        stdout="23 passed, 2 failed\n",
        stderr="",
        failed_tests=[
            "tests/test_auth.py::test_login",
            "tests/test_auth.py::test_refresh",
        ],
        total_tests=25,
        passed_tests=23,
        skipped_tests=0,
    )

    assert result.success is False
    assert result.exit_code == 1

    assert result.failure_count == 2
    assert result.has_failures is True


def test_result_with_no_test_counts():
    result = TestResult(
        success=False,
        exit_code=1,
        duration_ms=500,
        stderr="pytest: command not found",
    )

    assert result.total_tests is None
    assert result.passed_tests is None
    assert result.skipped_tests is None

    assert result.failed_tests == []


def test_default_output_values():
    result = TestResult(
        success=True,
        exit_code=0,
        duration_ms=100,
    )

    assert result.stdout == ""
    assert result.stderr == ""
    assert result.failed_tests == []


def test_negative_duration_rejected():
    with pytest.raises(ValidationError):
        TestResult(
            success=True,
            exit_code=0,
            duration_ms=-1,
        )


def test_negative_total_tests_rejected():
    with pytest.raises(ValidationError):
        TestResult(
            success=True,
            exit_code=0,
            duration_ms=100,
            total_tests=-1,
        )


def test_negative_passed_tests_rejected():
    with pytest.raises(ValidationError):
        TestResult(
            success=True,
            exit_code=0,
            duration_ms=100,
            passed_tests=-1,
        )


def test_negative_skipped_tests_rejected():
    with pytest.raises(ValidationError):
        TestResult(
            success=True,
            exit_code=0,
            duration_ms=100,
            skipped_tests=-1,
        )
