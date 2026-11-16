import uuid

from sqlalchemy.orm import Session

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.schemas.project import ProjectCreate
from app.database.repositories import project_repository


from app.schemas.project import ProjectUpdate
from app.database.repositories import project_repository


from app.database.repositories.project_repository import (
    get_projects_by_organization,
)


def list_organization_projects(
    db: Session,
    organization_id: uuid.UUID
):
    return get_projects_by_organization(db, organization_id)



def create_new_project(db: Session, data: ProjectCreate):

    organization = project_repository.get_organization(
        db,
        data.organization_id
    )

    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    existing_project = project_repository.get_project_by_key(
        db,
        data.organization_id,
        data.project_key
    )

    if existing_project is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project key already exists in this organization"
        )

    try:
        return project_repository.create_project(
            db,
            data.model_dump()
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project could not be created because of a uniqueness conflict"
        )




def get_project_details(
    db: Session,
    project_id: uuid.UUID
):
    project = project_repository.get_project_by_id(
        db,
        project_id
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    return project


def update_existing_project(
    db: Session,
    project_id: uuid.UUID,
    data: ProjectUpdate
):
    project = get_project_details(db, project_id)

    if project.status == "archived":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Archived projects cannot be updated"
        )

    update_data = data.model_dump(exclude_unset=True)

    # Prevent setting non-nullable database columns to NULL.
    for field in ("name", "methodology", "status"):
        if field in update_data and update_data[field] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{field} cannot be null"
            )

    return project_repository.update_project(
        db,
        project,
        update_data
    )


def archive_existing_project(
    db: Session,
    project_id: uuid.UUID
):
    project = get_project_details(db, project_id)

    if project.status == "archived":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project is already archived"
        )

    return project_repository.archive_project(
        db,
        project
    )