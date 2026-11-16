import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sprint import Sprint
from app.models.sprint_commitment import SprintCommitment
from app.models.work_item import WorkItem


def get_completed_sprints(
    db: Session,
    project_id: uuid.UUID
):
    statement = (
        select(Sprint)
        .where(
            Sprint.project_id == project_id,
            Sprint.status == "completed"
        )
        .order_by(Sprint.end_date.asc(), Sprint.id.asc())
    )

    return list(db.scalars(statement).all())


def get_sprint_commitment_details(
    db: Session,
    sprint_id: uuid.UUID
):
    statement = (
        select(SprintCommitment, WorkItem)
        .join(
            WorkItem,
            SprintCommitment.work_item_id == WorkItem.id
        )
        .where(SprintCommitment.sprint_id == sprint_id)
    )

    return db.execute(statement).all()