import pytest
from uuid import UUID

from app.models.enums import ProjectStatus
from app.models.project import Project


@pytest.fixture
def project_factory(db_session, workspace):
    """
    Factory for creating Project instances.
    """

    def factory(
        *,
        workspace_id: UUID | None = None,
        name: str = "Test Project",
        description: str = "Sample description for project",
        primary_language: str | None = None,
        status: ProjectStatus = ProjectStatus.ACTIVE,
    ) -> Project:
        project = Project(
            workspace_id=(workspace.id if workspace_id is None else workspace_id),
            name=name,
            description=description,
            primary_language=primary_language,
            status=status,
        )

        db_session.add(project)
        db_session.flush()

        return project

    return factory


@pytest.fixture
def project(project_factory):
    return project_factory()
