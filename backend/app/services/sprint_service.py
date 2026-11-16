import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from sqlalchemy import select
from app.models.sprint import Sprint
from app.database.repositories import sprint_commitment_repository

from app.models.project import Project
from app.models.team import Team
from app.schemas.sprint import SprintCreate
from app.database.repositories import sprint_repository

from datetime import date
from app.schemas.sprint import SprintUpdate


def list_project_sprints(
    db: Session,
    project_id: uuid.UUID
):
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    return sprint_repository.get_sprints_by_project(
        db,
        project_id
    )


def create_new_sprint(
    db: Session,
    data: SprintCreate
):
    project = db.get(Project, data.project_id)
    team = db.get(Team, data.team_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    if team is None:
        raise HTTPException(
            status_code=404,
            detail="Team not found"
        )

    if project.status == "archived":
        raise HTTPException(
            status_code=409,
            detail="Cannot create a sprint in an archived project"
        )

    if project.organization_id != team.organization_id:
        raise HTTPException(
            status_code=422,
            detail="Project and team must belong to the same organization"
        )

    association = sprint_repository.get_project_team(
        db,
        data.project_id,
        data.team_id
    )

    if association is None:
        raise HTTPException(
            status_code=422,
            detail="Team is not assigned to this project"
        )

    existing = sprint_repository.get_sprint_by_name(
        db,
        data.project_id,
        data.team_id,
        data.name
    )

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="Sprint name already exists for this project and team"
        )

    try:
        return sprint_repository.create_sprint(
            db,
            data.model_dump()
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Sprint could not be created due to a database constraint"
        )

def get_sprint_details(
    db: Session,
    sprint_id: uuid.UUID
):
    sprint = sprint_repository.get_sprint_by_id(
        db, sprint_id
    )

    if sprint is None:
        raise HTTPException(
            status_code=404,
            detail="Sprint not found"
        )

    return sprint


def update_existing_sprint(
    db: Session,
    sprint_id: uuid.UUID,
    data: SprintUpdate
):
    sprint = get_sprint_details(db, sprint_id)

    if sprint.status != "planned":
        raise HTTPException(
            status_code=409,
            detail="Only planned sprints can be edited"
        )

    changes = data.model_dump(exclude_unset=True)

    for field in ("name", "start_date", "end_date"):
        if field in changes and changes[field] is None:
            raise HTTPException(
                status_code=422,
                detail=f"{field} cannot be null"
            )

    start = changes.get("start_date", sprint.start_date)
    end = changes.get("end_date", sprint.end_date)

    if end < start:
        raise HTTPException(
            status_code=422,
            detail="Sprint end date cannot be before start date"
        )

    if "name" in changes:
        existing = sprint_repository.get_sprint_by_name(
            db,
            sprint.project_id,
            sprint.team_id,
            changes["name"]
        )

        if existing is not None and existing.id != sprint.id:
            raise HTTPException(
                status_code=409,
                detail="Sprint name already exists"
            )

    for field, value in changes.items():
        setattr(sprint, field, value)

    try:
        return sprint_repository.save_sprint(db, sprint)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Sprint update conflicts with a database constraint"
        )


ALLOWED_TRANSITIONS = {
    "planned": {"active", "cancelled"},
    "active": {"completed", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}


def transition_sprint(
    db: Session,
    sprint_id: uuid.UUID,
    target_status: str
):
    sprint = get_sprint_details(db, sprint_id)

    allowed = ALLOWED_TRANSITIONS.get(
        sprint.status, set()
    )

    if target_status not in allowed:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Cannot transition sprint from "
                f"'{sprint.status}' to '{target_status}'"
            )
        )

    project = db.get(Project, sprint.project_id)

    if project is None or project.status == "archived":
        raise HTTPException(
            status_code=409,
            detail="Cannot change sprint lifecycle in an archived or missing project"
        )

    sprint.status = target_status

    return sprint_repository.save_sprint(db, sprint)

def start_sprint_with_commitment(
    db: Session,
    sprint_id: uuid.UUID
):
    try:
        # Lock the sprint row to prevent simultaneous start requests.
        sprint = db.scalar(
            select(Sprint)
            .where(Sprint.id == sprint_id)
            .with_for_update()
        )

        if sprint is None:
            raise HTTPException(
                status_code=404,
                detail="Sprint not found"
            )

        if sprint.status != "planned":
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Cannot start sprint with status "
                    f"'{sprint.status}'"
                )
            )

        project = db.get(Project, sprint.project_id)

        if project is None or project.status == "archived":
            raise HTTPException(
                status_code=409,
                detail="Cannot start a sprint in an archived or missing project"
            )

        work_items = (
            sprint_commitment_repository.get_committable_work_items(
                db,
                sprint_id
            )
        )

        sprint_commitment_repository.create_commitment_snapshots(
            db,
            sprint_id,
            work_items
        )

        sprint.status = "active"
        db.add(sprint)

        # One atomic commit for the sprint and all commitments.
        db.commit()
        db.refresh(sprint)

        return sprint

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Sprint commitment conflicts with existing records"
        )

    except Exception:
        db.rollback()
        raise


def list_sprint_commitments(
    db: Session,
    sprint_id: uuid.UUID
):
    get_sprint_details(db, sprint_id)

    return sprint_commitment_repository.get_sprint_commitments(
        db,
        sprint_id
    )