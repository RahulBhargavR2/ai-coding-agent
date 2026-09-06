from app.ai.agents.reviewer import ReviewerAgent
from app.ai.llm.provider import MockLLMProvider
from app.ai.models.changes import (
    ChangeAction,
    ProposedChange,
)
from app.ai.models.review import ReviewStatus
from app.retrieval.models import RetrievedChunk


def test_reviewer_approves_valid_changes():
    llm = MockLLMProvider(
        response="""
        {
            "status": "approved",
            "summary": "The proposed changes satisfy the request.",
            "findings": []
        }
        """
    )

    agent = ReviewerAgent(llm)

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
    }

    result = agent.run(state)

    review = result["review_result"]

    assert result["status"] == "reviewed"
    assert result["current_step"] == "reviewer"

    assert review.status == ReviewStatus.APPROVED
    assert review.summary == ("The proposed changes satisfy the request.")
    assert review.findings == []


def test_reviewer_rejects_invalid_changes():
    llm = MockLLMProvider(
        response="""
        {
            "status": "changes_required",
            "summary": "Authentication validation is incomplete.",
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

    agent = ReviewerAgent(llm)

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
    }

    result = agent.run(state)

    review = result["review_result"]

    assert review.status == ReviewStatus.CHANGES_REQUIRED

    assert len(review.findings) == 1

    finding = review.findings[0]

    assert finding.severity == "error"
    assert finding.file_path == "app/auth/jwt.py"
    assert "expiration" in finding.message
