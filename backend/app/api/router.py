from fastapi import APIRouter

from app.api.v1 import (
    auth,
    workspace,
    project,
    repository,
)


api_router = APIRouter(
    prefix="/api/v1",
)

api_router.include_router(auth.router)
api_router.include_router(workspace.router)
api_router.include_router(project.router)
api_router.include_router(repository.router)
