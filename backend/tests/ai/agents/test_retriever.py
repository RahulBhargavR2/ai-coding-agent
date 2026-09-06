from uuid import uuid4

from app.ai.agents.retriever import RetrieverAgent
from app.retrieval.models import RetrievedChunk, RetrievalResult


class FakeRetriever:
    def __init__(self) -> None:
        self.received_query = None

    def retrieve(self, query):
        self.received_query = query

        return RetrievalResult(
            query=query.query,
            chunks=[
                RetrievedChunk(
                    id="chunk-1",
                    content="JWT authentication implementation",
                    score=0.95,
                    relative_path="app/auth/jwt.py",
                    language="python",
                    start_line=1,
                    end_line=20,
                    symbol_name="JWTService",
                    metadata={},
                )
            ],
        )


def test_retriever_returns_repository_context():
    repository_id = uuid4()

    retriever = FakeRetriever()

    agent = RetrieverAgent(
        retriever=retriever,
        limit=10,
    )

    state = {
        "user_request": "Add JWT authentication",
        "repository_id": repository_id,
        "plan": [
            "Inspect existing authentication",
            "Implement JWT",
            "Add authentication tests",
        ],
    }

    result = agent.run(state)

    assert result["status"] == "retrieved"
    assert result["current_step"] == "retriever"

    assert len(result["retrieved_context"]) == 1

    chunk = result["retrieved_context"][0]

    assert chunk.relative_path == "app/auth/jwt.py"
    assert chunk.symbol_name == "JWTService"

    assert retriever.received_query.repository_id == repository_id
    assert retriever.received_query.limit == 10

    assert "Add JWT authentication" in (retriever.received_query.query)

    assert "Implement JWT" in (retriever.received_query.query)
