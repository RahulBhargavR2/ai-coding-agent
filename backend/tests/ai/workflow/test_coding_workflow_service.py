from uuid import uuid4

from app.ai.workflows.coding_workflow import CodingWorkflowService
import pytest

class FakeWorkflow:
    def __init__(self) -> None:
        self.called = False
        self.received_state = None

    def build(self):
        return self

    def ainvoke(self, state):
        self.called = True
        self.received_state = state

        return {
            "status": "completed",
        }


@pytest.mark.asyncio
async def test_coding_workflow_service_runs_workflow() -> None:
    workflow = FakeWorkflow()
    service = CodingWorkflowService(workflow=workflow)

    state = {
        "user_request": "Add a health endpoint.",
        "repository_id": uuid4(),
        "iteration_count": 0,
    }

    result = await service.run(state)
    print(workflow.called)

    assert workflow.called is True
    assert workflow.received_state == state
    assert result == {
        "status": "completed",
    }
