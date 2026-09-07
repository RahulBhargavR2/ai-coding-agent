from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Response,
    UploadFile,
    status,
)

from pathlib import Path
from tempfile import NamedTemporaryFile

from app.dependencies.auth import  CurrentActiveUser
from app.dependencies.uow import UnitOfWorkDep
from app.dependencies.indexing import RepositoryIndexingServiceDep
from app.models.user import User
from app.schemas.repository import (
    GithubRepositoryCreate,
    RepositoryResponse,
    UploadRepositoryCreate,
    RepositoryIndexResponse,
    RepositoryIndexStatusResponse
)
from app.services.workspace.repository_service import RepositoryService
from app.services.workspace.repository_indexing_service import RepositoryIndexingService

router = APIRouter(
    prefix="/repositories",
    tags=["Repositories"],
)


@router.post(
    "/import/github",
    response_model=RepositoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def import_github_repository(
    request: GithubRepositoryCreate,
    current_user: CurrentActiveUser,
    uow: UnitOfWorkDep,
) -> RepositoryResponse:

    service = RepositoryService(uow)

    return service.create_github_repository(
        user_id=current_user.id,
        data=request,
    )


@router.get(
    "/{repository_id}",
    response_model=RepositoryResponse,
)
def get_repository(
    repository_id: UUID,
    current_user: CurrentActiveUser,
    uow: UnitOfWorkDep,
) -> RepositoryResponse:

    service = RepositoryService(uow)

    return service.get_repository(
        repository_id=repository_id,
        user_id=current_user.id,
    )


@router.get(
    "/project/{project_id}",
    response_model=list[RepositoryResponse],
)
def list_project_repositories(
    project_id: UUID,
    current_user:  CurrentActiveUser,
    uow: UnitOfWorkDep,
) -> list[RepositoryResponse]:

    service = RepositoryService(uow)

    return service.list_project_repositories(
        project_id=project_id,
        user_id=current_user.id,
    )


@router.delete(
    "/{repository_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_repository(
    repository_id: UUID,
    current_user: CurrentActiveUser,
    uow: UnitOfWorkDep,
) -> Response:

    service = RepositoryService(uow)

    service.delete_repository(
        repository_id=repository_id,
        user_id=current_user.id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


@router.post(
    "/{repository_id}/index",
    response_model=RepositoryIndexResponse,
    status_code=status.HTTP_200_OK,
)
def index_repository(
    repository_id: UUID,
    current_user: CurrentActiveUser,
    indexing_service: RepositoryIndexingServiceDep 
) -> RepositoryIndexResponse:
    """
    Import and incrementally index a GitHub repository.
    """

    result = indexing_service.index_repository(
        repository_id=repository_id,
        user_id=current_user.id,
    )

    return RepositoryIndexResponse(
        repository_id=result.repository_id,
        files_discovered=result.files_discovered,
        files_indexed=result.files_indexed,
        chunks_created=result.chunks_created,
        embeddings_created=result.embeddings_created,
    )


@router.post(
    "/upload",
    response_model=RepositoryIndexResponse,
    status_code=status.HTTP_200_OK,
)
def upload_repository(
    project_id: UUID = Form(...),
    name: str = Form(...),
    file: UploadFile = File(...),
    *,
    current_user: CurrentActiveUser,
    uow: UnitOfWorkDep,
    indexing_service: RepositoryIndexingServiceDep,
) -> RepositoryIndexResponse:
    """
    Upload a ZIP repository and index it.
    """

    if not file.filename:
        raise BusinessValidationError("Repository archive must have a filename.")

    if not file.filename.lower().endswith(".zip"):
        raise BusinessValidationError("Only ZIP repository archives are supported.")

    temporary_path: Path | None = None

    try:
        repository_service = RepositoryService(uow)
        with NamedTemporaryFile(
            suffix=".zip",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)

            while chunk := file.file.read(1024 * 1024):
                temporary_file.write(chunk)

        repository = repository_service.create_uploaded_repository(
            user_id=current_user.id,
            data=UploadRepositoryCreate(
                project_id=project_id,
                name=name,
            ),
        )

        result = indexing_service.index_repository(
            repository_id=repository.id,
            user_id=current_user.id,
            archive_path=temporary_path,
        )

        return RepositoryIndexResponse(
            repository_id=result.repository_id,
            files_discovered=result.files_discovered,
            files_added=result.files_added,
            files_modified=result.files_modified,
            files_unchanged=result.files_unchanged,
            files_deleted=result.files_deleted,
            files_indexed=result.files_indexed,
            chunks_created=result.chunks_created,
            embeddings_created=result.embeddings_created,
        )

    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


@router.get(
    "/{repository_id}/index/status",
    response_model=RepositoryIndexStatusResponse,
)
def get_repository_index_status(
    repository_id: UUID,
    current_user: CurrentActiveUser,
    uow:UnitOfWorkDep
) -> RepositoryIndexStatusResponse:
    """
    Retrieve the indexing status of a repository.
    """
    repository_service = RepositoryService(uow)

    repository = repository_service.get_repository(
        repository_id=repository_id,
        user_id=current_user.id,
    )

    return RepositoryIndexStatusResponse(
        repository_id=repository.id,
        status=repository.status,
        last_indexed_at=repository.last_indexed_at,
    )
