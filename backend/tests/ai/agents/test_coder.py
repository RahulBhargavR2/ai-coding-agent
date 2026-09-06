from uuid import uuid4

from app.ai.agents.coder import CoderAgent
from app.ai.llm.provider import MockLLMProvider
from app.ai.models.changes import ChangeAction
from app.retrieval.models import RetrievedChunk

from tests.ai.agents.capture_llm import CapturingLLM


def test_coder_creates_proposed_changes():
    llm = MockLLMProvider(
        response="""
        {
            "changes": [
                {
                    "relative_path": "app/auth/jwt.py",
                    "action": "create",
                    "content": "class JWTService:\\n    pass",
                    "reason": "Add JWT service"
                }
            ]
        }
        """
    )

    agent = CoderAgent(llm)

    repository_id = uuid4()

    state = {
        "user_request": "Add JWT authentication",
        "repository_id": repository_id,
        "plan": [
            "Inspect authentication",
            "Implement JWT",
            "Add tests",
        ],
        "retrieved_context": [
            RetrievedChunk(
                id="chunk-1",
                content="existing authentication code",
                score=0.95,
                relative_path="app/auth/service.py",
                language="python",
                start_line=1,
                end_line=20,
                symbol_name="AuthenticationService",
                metadata={},
            )
        ],
    }

    result = agent.run(state)

    assert result["status"] == "coded"
    assert result["current_step"] == "coder"

    assert len(result["proposed_changes"]) == 1

    change = result["proposed_changes"][0]

    assert change.relative_path == "app/auth/jwt.py"
    assert change.action == ChangeAction.CREATE
    assert change.content == "class JWTService:\n    pass"
    assert change.reason == "Add JWT service"


def test_coder_receives_plan_and_repository_context():
    llm = CapturingLLM(
        response='{"changes": []}',
    )

    agent = CoderAgent(llm)

    state = {
        "user_request": "Add JWT authentication",
        "plan": [
            "Inspect authentication",
            "Implement JWT",
        ],
        "retrieved_context": [
            RetrievedChunk(
                id="chunk-1",
                content="class AuthenticationService:",
                score=0.9,
                relative_path="app/auth/service.py",
                language="python",
                start_line=1,
                end_line=10,
                symbol_name="AuthenticationService",
                metadata={},
            )
        ],
    }

    agent.run(state)

    assert "Add JWT authentication" in llm.user_prompt
    assert "Implement JWT" in llm.user_prompt
    assert "app/auth/service.py" in llm.user_prompt
    assert "AuthenticationService" in llm.user_prompt
