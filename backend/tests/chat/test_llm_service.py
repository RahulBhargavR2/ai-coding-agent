from types import SimpleNamespace

from app.services.chat.llm_service import (
    LLMMessage,
    LLMRequest,
    LLMService,
)


def make_client(response):
    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=lambda **kwargs: response)
        )
    )

    return client


def test_generate_returns_llm_response():
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="Hello from LLM"))],
        model="test-model",
        usage=SimpleNamespace(
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
        ),
    )

    service = LLMService(
        client=make_client(response),
        model="test-model",
    )

    request = LLMRequest(
        messages=[
            LLMMessage(
                role="user",
                content="Hello",
            )
        ],
        temperature=0.2,
    )

    result = service.generate(request)

    assert result.content == "Hello from LLM"
    assert result.model == "test-model"

    assert result.usage == {
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "total_tokens": 15,
    }


def test_generate_handles_empty_content():
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=None))],
        model="test-model",
        usage=None,
    )

    service = LLMService(
        client=make_client(response),
        model="test-model",
    )

    request = LLMRequest(
        messages=[
            LLMMessage(
                role="user",
                content="Hello",
            )
        ]
    )

    result = service.generate(request)

    assert result.content == ""
    assert result.model == "test-model"
    assert result.usage is None


def test_build_llm_messages_contains_system_prompt():
    messages = LLMService.build_llm_messages(
        system_prompt="You are a coding assistant.",
        history=[],
        repository_context="",
        user_message="Explain this code.",
    )

    assert messages[0].role == "system"
    assert messages[0].content == "You are a coding assistant."

    assert messages[-1].role == "user"
    assert messages[-1].content == "Explain this code."


def test_build_llm_messages_includes_history():
    history = [
        SimpleNamespace(
            role=SimpleNamespace(value="user"),
            content="Previous question",
        ),
        SimpleNamespace(
            role=SimpleNamespace(value="assistant"),
            content="Previous answer",
        ),
    ]

    messages = LLMService.build_llm_messages(
        system_prompt="System",
        history=history,
        repository_context="",
        user_message="Current question",
    )

    assert messages[1].role == "user"
    assert messages[1].content == "Previous question"

    assert messages[2].role == "assistant"
    assert messages[2].content == "Previous answer"


def test_build_llm_messages_includes_repository_context():
    messages = LLMService.build_llm_messages(
        system_prompt="System",
        history=[],
        repository_context="File: app/main.py\nhello()",
        user_message="Explain hello.",
    )

    assert len(messages) == 3

    assert messages[1].role == "system"
    assert "repository context" in messages[1].content
    assert "app/main.py" in messages[1].content

    assert messages[2].role == "user"
    assert messages[2].content == "Explain hello."
