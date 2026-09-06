from uuid import uuid4

from app.ai.agents.summarizer import SummarizerAgent
from app.ai.llm.provider import MockLLMProvider
from app.ai.models.summary import SummaryResult


def test_summarizer_returns_summary() -> None:
    llm = MockLLMProvider(response="Implemented the requested change successfully.")

    agent = SummarizerAgent(llm)

    state = {
        "user_request": "Add a health check endpoint.",
        "repository_id": uuid4(),
        "plan": [
            "Create the health check route",
            "Add tests",
        ],
        "proposed_changes": [],
    }

    result = agent.run(state)

    assert isinstance(result["summary"], SummaryResult)
    assert result["summary"].summary == "Implemented the requested change successfully."
    assert result["current_step"] == "summarizer"
    assert result["status"] == "completed"
