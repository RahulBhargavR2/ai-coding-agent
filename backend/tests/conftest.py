"""
Global pytest configuration.

This file registers all fixture modules used across the test suite.
"""

pytest_plugins = [
    "tests.fixtures.database",
    "tests.fixtures.client",
    "tests.fixtures.user",
    "tests.fixtures.auth",
]
