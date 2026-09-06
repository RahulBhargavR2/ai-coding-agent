from app.ai.agents.critic import CriticAgent
from app.ai.llm.provider import MockLLMProvider
from app.ai.models.changes import (
    ChangeAction,
    ProposedChange,
)
from app.ai.models.critique import CritiqueDecision
from app.ai.models.review import (
    ReviewResult,
    ReviewStatus,
)
from app.retrieval.models import RetrievedChunk

from tests.ai.agents.capture_llm import CapturingLLM

def test_critic_approves_safe_changes():
    llm = MockLLMProvider(
        response="""
        {
            "decision": "approve",
            "summary": "No significant issues were identified.",
            "findings": []
        }
        """
    )

    agent = CriticAgent(llm)

    state = {
        "user_request": "Add JWT authentication",
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
        "proposed_changes": [
            ProposedChange(
                relative_path="app/auth/jwt.py",
                action=ChangeAction.CREATE,
                content="class JWTService:\n    pass",
                reason="Add JWT service",
            )
        ],
        "review_result": ReviewResult(
            status=ReviewStatus.APPROVED,
            summary="The proposed changes satisfy the request.",
            findings=[],
        ),
    }

    result = agent.run(state)

    critique = result["critique"]

    assert result["status"] == "criticized"
    assert result["current_step"] == "critic"

    assert critique.decision == CritiqueDecision.APPROVE
    assert critique.findings == []


def test_critic_rejects_problematic_changes():
    llm = CapturingLLM(
        response="""
        {
            "decision": "reject",
            "summary": "The implementation has a security issue.",
            "findings": [
                {
                    "severity": "error",
                    "file_path": "app/auth/jwt.py",
                    "message": "Token expiration is not validated."
                }
            ]
        }
        """
    )

    agent = CriticAgent(llm)

    state = {
        "user_request": "Add JWT authentication",
        "plan": [
            "Implement JWT",
        ],
        "retrieved_context": [],
        "proposed_changes": [
            ProposedChange(
                relative_path="app/auth/jwt.py",
                action=ChangeAction.CREATE,
                content="class JWTService:\n    pass",
                reason="Add JWT service",
            )
        ],
        "review_result": ReviewResult(
            status=ReviewStatus.APPROVED,
            summary="The implementation looks correct.",
            findings=[],
        ),
    }

    result = agent.run(state)

    critique = result["critique"]

    assert critique.decision == CritiqueDecision.REJECT

    assert len(critique.findings) == 1

    finding = critique.findings[0]

    assert finding.severity == "error"
    assert finding.file_path == "app/auth/jwt.py"
    assert "expiration" in finding.message

    assert "The implementation looks correct." in llm.user_prompt
    assert "app/auth/jwt.py" in llm.user_prompt
    assert "Add JWT authentication" in llm.user_prompt
