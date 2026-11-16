import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.schemas.work_item import WorkItemSprintAssignment
from app.services.work_item_service import assign_work_item_to_sprint

from app.database.connection import get_db
from app.schemas.work_item import WorkItemCreate, WorkItemResponse
from app.services.work_item_service import (
    create_new_work_item,
    list_project_work_items,
)
from app.schemas.work_item import (
    WorkItemUpdate,
    WorkItemTransition,
    WorkItemStateHistoryResponse,
)

from app.services.work_item_service import (
    get_work_item_details,
    update_existing_work_item,
    transition_existing_work_item,
    list_work_item_history,
)

router = APIRouter(
    prefix="/work-items",
    tags=["Work Items"]
)


@router.post(
    "/",
    response_model=WorkItemResponse,
    status_code=status.HTTP_201_CREATED
)
def create_work_item(
    data: WorkItemCreate,
    db: Session = Depends(get_db)
):
    return create_new_work_item(db, data)


@router.get(
    "/",
    response_model=list[WorkItemResponse]
)
def list_work_items(
    project_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    return list_project_work_items(db, project_id)


@router.get(
    "/{work_item_id}",
    response_model=WorkItemResponse
)
def get_work_item(
    work_item_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    return get_work_item_details(db, work_item_id)


@router.patch(
    "/{work_item_id}",
    response_model=WorkItemResponse
)
def patch_work_item(
    work_item_id: uuid.UUID,
    data: WorkItemUpdate,
    db: Session = Depends(get_db)
):
    return update_existing_work_item(
        db, work_item_id, data
    )


@router.post(
    "/{work_item_id}/transition",
    response_model=WorkItemResponse
)
def transition_work_item(
    work_item_id: uuid.UUID,
    data: WorkItemTransition,
    db: Session = Depends(get_db)
):
    return transition_existing_work_item(
        db, work_item_id, data
    )


@router.get(
    "/{work_item_id}/history",
    response_model=list[WorkItemStateHistoryResponse]
)
def get_work_item_history(
    work_item_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    return list_work_item_history(
        db, work_item_id
    )




@router.patch(
    "/{work_item_id}/sprint",
    response_model=WorkItemResponse
)
def patch_work_item_sprint(
    work_item_id: uuid.UUID,
    data: WorkItemSprintAssignment,
    db: Session = Depends(get_db)
):
    return assign_work_item_to_sprint(
        db,
        work_item_id,
        data
    )