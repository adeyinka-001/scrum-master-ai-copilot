import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.services.sprint_service import start_sprint_with_commitment

from app.schemas.sprint_commitment import SprintCommitmentResponse
from app.services.sprint_service import list_sprint_commitments

from app.database.connection import get_db
from app.schemas.sprint import SprintCreate, SprintResponse
from app.services.sprint_service import (
    create_new_sprint,
    list_project_sprints,
)

from app.schemas.sprint import SprintUpdate
from app.services.sprint_service import (
    get_sprint_details,
    update_existing_sprint,
    transition_sprint,
)

router = APIRouter(
    prefix="/sprints",
    tags=["Sprints"]
)


@router.post(
    "/",
    response_model=SprintResponse,
    status_code=status.HTTP_201_CREATED
)
def create_sprint(
    sprint: SprintCreate,
    db: Session = Depends(get_db)
):
    return create_new_sprint(db, sprint)


@router.get(
    "/",
    response_model=list[SprintResponse]
)
def list_sprints(
    project_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    return list_project_sprints(db, project_id)

@router.get(
    "/{sprint_id}",
    response_model=SprintResponse
)
def get_sprint(
    sprint_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    return get_sprint_details(db, sprint_id)


@router.patch(
    "/{sprint_id}",
    response_model=SprintResponse
)
def patch_sprint(
    sprint_id: uuid.UUID,
    data: SprintUpdate,
    db: Session = Depends(get_db)
):
    return update_existing_sprint(
        db, sprint_id, data
    )


@router.post(
    "/{sprint_id}/start",
    response_model=SprintResponse
)
def start_sprint(
    sprint_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    return start_sprint_with_commitment(
        db,
        sprint_id
    )


@router.post(
    "/{sprint_id}/complete",
    response_model=SprintResponse
)
def complete_sprint(
    sprint_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    return transition_sprint(
        db, sprint_id, "completed"
    )


@router.post(
    "/{sprint_id}/cancel",
    response_model=SprintResponse
)
def cancel_sprint(
    sprint_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    return transition_sprint(
        db, sprint_id, "cancelled"
    )




@router.get(
    "/{sprint_id}/commitments",
    response_model=list[SprintCommitmentResponse]
)
def get_sprint_commitments(
    sprint_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    return list_sprint_commitments(
        db,
        sprint_id
    )