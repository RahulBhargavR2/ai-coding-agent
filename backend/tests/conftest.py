"""
Global pytest configuration.

This file registers all fixture modules used across the test suite.
"""

pytest_plugins = [
    "tests.fixtures.database",
    "tests.fixtures.client",
    "tests.fixtures.user",
    "tests.fixtures.workspace",
    "tests.fixtures.projects",
    "tests.fixtures.repositories",
    "tests.fixtures.chats",
    "tests.fixtures.chat_message",
    "tests.fixtures.auth",
]
