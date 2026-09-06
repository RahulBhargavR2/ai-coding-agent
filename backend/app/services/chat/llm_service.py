from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class LLMMessage:
    """
    Provider-independent representation of an LLM message.
    """

    role: str
    content: str


@dataclass(frozen=True)
class LLMRequest:
    """
    Represents a request sent to the language model.
    """

    messages: Sequence[LLMMessage]
    temperature: float = 0.2
    max_tokens: int | None = None


@dataclass(frozen=True)
class LLMResponse:
    """
    Represents the normalized response returned by the LLM.
    """

    content: str
    model: str | None = None
    usage: dict[str, int] | None = None


class LLMService:
    """
    Provider-independent interface for language-model generation.

    The actual provider implementation will be injected into this
    service later.
    """

    def __init__(
        self,
        client,
        model: str,
    ) -> None:
        self.client = client
        self.model = model

    def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        """
        Generate a response from the configured language model.
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": message.role,
                    "content": message.content,
                }
                for message in request.messages
            ],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        content = response.choices[0].message.content

        if not content:
            content = ""

        usage = None

        if response.usage is not None:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return LLMResponse(
            content=content,
            model=response.model,
            usage=usage,
        )

    def build_llm_messages(
        *,
        system_prompt: str,
        history,
        repository_context: str,
        user_message: str,
    ) -> list[LLMMessage]:
        """
        Construct the ordered message list sent to the LLM.
        """

        messages: list[LLMMessage] = [
            LLMMessage(
                role="system",
                content=system_prompt,
            )
        ]

        for message in history:
            messages.append(
                LLMMessage(
                    role=message.role.value,
                    content=message.content,
                )
            )

        if repository_context:
            messages.append(
                LLMMessage(
                    role="system",
                    content=(
                        "The following repository context was "
                        "retrieved for the current request.\n\n"
                        f"{repository_context}"
                    ),
                )
            )

        messages.append(
            LLMMessage(
                role="user",
                content=user_message,
            )
        )

        return messages