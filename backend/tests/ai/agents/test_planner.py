from app.ai.agents.planner import PlannerAgent
from app.ai.llm.provider import MockLLMProvider


def test_planner_creates_plan():
    llm = MockLLMProvider(
        response='{"plan": ["Inspect authentication", "Implement JWT", "Add tests"]}'
    )

    planner = PlannerAgent(llm)

    state = {
        "user_request": "Add JWT authentication",
    }

    result = planner.run(state)

    assert result["plan"] == [
        "Inspect authentication",
        "Implement JWT",
        "Add tests",
    ]

    assert result["status"] == "planned"
