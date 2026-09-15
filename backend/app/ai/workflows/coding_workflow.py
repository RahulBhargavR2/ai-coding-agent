from typing import Any

from app.ai.workflows.graph import CodingWorkflow
from app.ai.workflows.state import CodingAgentState


class CodingWorkflowService:
    def __init__(self, workflow: CodingWorkflow) -> None:
        self.workflow = workflow

    async def run(self, state: CodingAgentState) -> dict[str, Any]:
        return self.workflow.build().ainvoke(state)
