import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.project import ProjectResponse
from app.services.project_service import list_organization_projects

from fastapi import status
from app.schemas.project import ProjectCreate
from app.services.project_service import create_new_project

from app.schemas.project import ProjectUpdate
from app.services.project_service import (
    get_project_details,
    update_existing_project,
    archive_existing_project,
)


router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)



@router.get(
    "/",
    response_model=list[ProjectResponse]
)
def list_projects(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    return list_organization_projects(
        db=db,
        organization_id=organization_id
    )



@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED
)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db)
):
    return create_new_project(db, project)


@router.get(
    "/{project_id}",
    response_model=ProjectResponse
)
def get_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    return get_project_details(
        db,
        project_id
    )


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse
)
def patch_project(
    project_id: uuid.UUID,
    data: ProjectUpdate,
    db: Session = Depends(get_db)
):
    return update_existing_project(
        db,
        project_id,
        data
    )


@router.delete(
    "/{project_id}",
    response_model=ProjectResponse
)
def delete_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    return archive_existing_project(
        db,
        project_id
    )