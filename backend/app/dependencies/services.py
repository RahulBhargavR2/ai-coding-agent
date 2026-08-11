from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.project_service import ProjectService
from app.services.workspace_service import WorkspaceService
from app.services.auth_service import AuthService
from app.unit_of_work import UnitOfWork
from app.services.repository_service import RepositoryService


def get_repository_service(
    db: Session = Depends(get_db),
) -> RepositoryService:
    return RepositoryService(UnitOfWork(db))


def get_project_service(
    db: Session = Depends(get_db),
) -> ProjectService:
    return ProjectService(UnitOfWork(db))


def get_workspace_service(
    db: Session = Depends(get_db),
) -> WorkspaceService:
    return WorkspaceService(UnitOfWork(db))


def get_auth_service(
    db: Session = Depends(get_db),
) -> AuthService:
    return AuthService(UnitOfWork(db))
