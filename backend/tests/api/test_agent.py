from app.dependencies.ai import get_coding_workflow_service
from app.ai.models.execution import ExecutionResult
from app.ai.models.summary import SummaryResult

base_url = "/api/v1"


class FakeCodingWorkflowService:
    def __init__(self):
        self.called = False
        self.received_state = None

    def run(self, state):
        self.called = True
        self.received_state = state

        return {
            "status": "completed",
            "execution_result": ExecutionResult(
                success=True,
                message="Dry-run execution completed.",
                executed_changes=["app/example.py"],
            ),
            "summary": SummaryResult(
                summary="Implemented the requested change.",
            ),
        }


def test_agent_task_success(
    client,
    user_factory,
    workspace_factory,
    project_factory,
    repository_factory,
):
    password = "CorrectPassword123!"

    user = user_factory(
        email="agent@example.com",
        password=password,
    )

    workspace = workspace_factory(
        user_id=user.id,
    )

    project = project_factory(
        workspace_id=workspace.id,
    )

    repository = repository_factory(
        project_id=project.id,
    )

    login_response = client.post(
        base_url + "/auth/login",
        json={
            "email": user.email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    fake_workflow = FakeCodingWorkflowService()

    client.app.dependency_overrides[get_coding_workflow_service] = lambda: fake_workflow

    try:
        response = client.post(
            base_url + "/agent/tasks",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
            json={
                "repository_id": str(repository.id),
                "request": "Add a health check endpoint",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["status"] == "completed"
        assert data["summary"] == "Implemented the requested change."

        assert data["execution"]["success"] is True
        assert data["execution"]["message"] == ("Dry-run execution completed.")
        assert data["execution"]["executed_changes"] == ["app/example.py"]

        assert fake_workflow.called is True

        assert fake_workflow.received_state["user_request"] == (
            "Add a health check endpoint"
        )
        assert fake_workflow.received_state["repository_id"] == repository.id
        assert fake_workflow.received_state["iteration_count"] == 0

    finally:
        client.app.dependency_overrides.pop(
            get_coding_workflow_service,
            None,
        )


def test_agent_task_without_token(
    client,
    repository,
):
    response = client.post(
        base_url + "/agent/tasks",
        json={
            "repository_id": str(repository.id),
            "request": "Add a health check endpoint",
        },
    )

    assert response.status_code == 401

    data = response.json()

    assert data["detail"] == ("Authentication credentials were not provided.")


def test_agent_task_forbidden_for_other_users_repository(
    client,
    user_factory,
    workspace_factory,
    project_factory,
    repository_factory,
):
    password = "CorrectPassword123!"

    owner = user_factory(
        email="repository-owner@example.com",
        password=password,
    )

    other_user = user_factory(
        email="other-user@example.com",
        password=password,
    )

    owner_workspace = workspace_factory(
        user_id=owner.id,
    )

    owner_project = project_factory(
        workspace_id=owner_workspace.id,
    )

    repository = repository_factory(
        project_id=owner_project.id,
    )

    login_response = client.post(
        base_url + "/auth/login",
        json={
            "email": other_user.email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.post(
        base_url + "/agent/tasks",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "repository_id": str(repository.id),
            "request": "Add a health check endpoint",
        },
    )

    assert response.status_code == 404
