from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """
    Abstraction over an LLM provider.
    """

    @abstractmethod
    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        **kwargs: Any,
    ) -> str:
        """
        Generate a response from the model.
        """
        raise NotImplementedError


class MockLLMProvider(LLMProvider):
    """
    Deterministic LLM implementation for testing.
    """

    def __init__(self, response: str = "mock response") -> None:
        self.response = response

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        **kwargs: Any,
    ) -> str:
        return self.response
