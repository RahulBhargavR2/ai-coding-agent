from fastapi import APIRouter

from app.dependencies.ai import CodingWorkflowServiceDep
from app.dependencies.auth import CurrentActiveUser
from app.dependencies.uow import UnitOfWorkDep
from app.schemas.agent import (
    AgentExecutionResponse,
    AgentTaskRequest,
    AgentTaskResponse,
)
from app.services.workspace.repository_service import RepositoryService


router = APIRouter(
    prefix="/agent",
    tags=["Agent"],
)


@router.post(
    "/tasks",
    response_model=AgentTaskResponse,
)
def create_agent_task(
    request: AgentTaskRequest,
    current_user: CurrentActiveUser,
    uow: UnitOfWorkDep,
    workflow_service: CodingWorkflowServiceDep,
) -> AgentTaskResponse:
    repository_service = RepositoryService(uow)

    repository_service.get_repository(
        repository_id=request.repository_id,
        user_id=current_user.id,
    )

    state = {
        "user_request": request.request,
        "repository_id": request.repository_id,
        "iteration_count": 0,
    }

    result = workflow_service.run(state)

    execution_result = result.get("execution_result")

    execution = None

    if execution_result is not None:
        execution = AgentExecutionResponse(
            success=execution_result.success,
            message=execution_result.message,
            executed_changes=execution_result.executed_changes,
        )

    summary_result = result.get("summary")

    summary = ""

    if summary_result is not None:
        summary = summary_result.summary

    return AgentTaskResponse(
        status=result.get("status", "completed"),
        summary=summary,
        execution=execution,
    )