import uuid

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.sprint import Sprint
from app.models.user import User
from app.models.work_item import WorkItem

from app.schemas.work_item import WorkItemCreate
from app.database.repositories import work_item_repository

from datetime import datetime, timezone

from app.schemas.work_item import WorkItemSprintAssignment

from app.models.work_item_state_history import WorkItemStateHistory
from app.schemas.work_item import (
    WorkItemUpdate,
    WorkItemTransition,
)

def list_project_work_items(
    db: Session,
    project_id: uuid.UUID
):
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    return work_item_repository.get_work_items_by_project(
        db,
        project_id
    )


def create_new_work_item(
    db: Session,
    data: WorkItemCreate
):
    project = db.get(Project, data.project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    if project.status == "archived":
        raise HTTPException(
            status_code=409,
            detail="Cannot add work items to an archived project"
        )

    if data.sprint_id is not None:
        sprint = db.get(Sprint, data.sprint_id)

        if sprint is None:
            raise HTTPException(
                status_code=404,
                detail="Sprint not found"
            )

        if sprint.project_id != data.project_id:
            raise HTTPException(
                status_code=422,
                detail="Sprint belongs to another project"
            )

        if sprint.status in {"completed", "cancelled"}:
            raise HTTPException(
                status_code=409,
                detail="Cannot add work items to a closed sprint"
            )

    if data.assigned_to is not None:
        user = db.get(User, data.assigned_to)

        if user is None:
            raise HTTPException(
                status_code=404,
                detail="Assigned user not found"
            )

    if data.parent_id is not None:
        parent = db.get(WorkItem, data.parent_id)

        if parent is None:
            raise HTTPException(
                status_code=404,
                detail="Parent work item not found"
            )

        if parent.project_id != data.project_id:
            raise HTTPException(
                status_code=422,
                detail="Parent work item belongs to another project"
            )

    try:
        return work_item_repository.create_work_item(
            db,
            data.model_dump()
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Work item could not be created due to a database constraint"
        )

## change this later - remove backlog and start with new
WORK_ITEM_TRANSITIONS = {
    "new": {"in_progress"},
    "in_progress": {"blocked", "new"},
    "blocked": {"in_progress", "done"},
    "done": {"in_progress"},
}


def get_work_item_details(
    db: Session,
    work_item_id: uuid.UUID
):
    work_item = work_item_repository.get_work_item_by_id(
        db, work_item_id
    )

    if work_item is None:
        raise HTTPException(
            status_code=404,
            detail="Work item not found"
        )

    return work_item


def update_existing_work_item(
    db: Session,
    work_item_id: uuid.UUID,
    data: WorkItemUpdate
):
    work_item = get_work_item_details(db, work_item_id)

    project = db.get(Project, work_item.project_id)

    if project is None or project.status == "archived":
        raise HTTPException(
            status_code=409,
            detail="Cannot update a work item in an archived or missing project"
        )

    changes = data.model_dump(exclude_unset=True)

    for field in ("title", "priority"):
        if field in changes and changes[field] is None:
            raise HTTPException(
                status_code=422,
                detail=f"{field} cannot be null"
            )

    for field, value in changes.items():
        setattr(work_item, field, value)

    return work_item_repository.save_work_item(
        db, work_item
    )


def transition_existing_work_item(
    db: Session,
    work_item_id: uuid.UUID,
    data: WorkItemTransition
):
    work_item = get_work_item_details(db, work_item_id)

    project = db.get(Project, work_item.project_id)

    if project is None or project.status == "archived":
        raise HTTPException(
            status_code=409,
            detail="Cannot transition a work item in an archived or missing project"
        )

    if work_item.sprint_id is not None:
        sprint = db.get(Sprint, work_item.sprint_id)

        if sprint is None or sprint.status in {
            "completed", "cancelled"
        }:
            raise HTTPException(
                status_code=409,
                detail="Cannot transition a work item in a closed or missing sprint"
            )

    allowed = WORK_ITEM_TRANSITIONS.get(
        work_item.state, set()
    )

    if data.new_state not in allowed:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Cannot transition work item from "
                f"'{work_item.state}' to '{data.new_state}'"
            )
        )

    if data.changed_by is not None:
        actor = db.get(User, data.changed_by)

        if actor is None:
            raise HTTPException(
                status_code=404,
                detail="User recording the change was not found"
            )

    previous_state = work_item.state
    now = datetime.now(timezone.utc)

    work_item.state = data.new_state

    if data.new_state == "done":
        work_item.completed_at = now
    elif previous_state == "done":
        work_item.completed_at = None

    history = WorkItemStateHistory(
        work_item_id=work_item.id,
        previous_state=previous_state,
        new_state=data.new_state,
        changed_at=now,
        changed_by=data.changed_by
    )

    try:
        return work_item_repository.save_work_item_transition(
            db,
            work_item,
            history
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Work item transition conflicts with a database constraint"
        )


def list_work_item_history(
    db: Session,
    work_item_id: uuid.UUID
):
    get_work_item_details(db, work_item_id)

    return work_item_repository.get_work_item_history(
        db, work_item_id
    )

def assign_work_item_to_sprint(
    db: Session,
    work_item_id: uuid.UUID,
    data: WorkItemSprintAssignment
):
    work_item = get_work_item_details(db, work_item_id)

    project = db.get(Project, work_item.project_id)

    if project is None or project.status == "archived":
        raise HTTPException(
            status_code=409,
            detail="Cannot reassign work items in an archived or missing project"
        )

    # Validate the current sprint before moving the work item.
    if work_item.sprint_id is not None:
        current_sprint = db.get(Sprint, work_item.sprint_id)

        if current_sprint is None or current_sprint.status in {
            "completed", "cancelled"
        }:
            raise HTTPException(
                status_code=409,
                detail="Cannot move work items out of a closed or missing sprint"
            )

    # Removing the work item from its sprint.
    if data.sprint_id is None:
        work_item.sprint_id = None

        return work_item_repository.save_work_item(
            db, work_item
        )

    # Assigning or moving to a sprint.
    sprint = db.get(Sprint, data.sprint_id)

    if sprint is None:
        raise HTTPException(
            status_code=404,
            detail="Target sprint not found"
        )

    if sprint.project_id != work_item.project_id:
        raise HTTPException(
            status_code=422,
            detail="Target sprint belongs to another project"
        )

    if sprint.status in {"completed", "cancelled"}:
        raise HTTPException(
            status_code=409,
            detail="Cannot assign work items to a closed sprint"
        )

    work_item.sprint_id = sprint.id

    return work_item_repository.save_work_item(
        db, work_item
    )