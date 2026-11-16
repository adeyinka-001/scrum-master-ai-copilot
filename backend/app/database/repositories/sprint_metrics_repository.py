import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sprint import Sprint
from app.models.work_item import WorkItem


def get_sprint(db: Session, sprint_id: uuid.UUID):
    return db.get(Sprint, sprint_id)


def get_sprint_work_items(
    db: Session,
    sprint_id: uuid.UUID
):
    statement = select(WorkItem).where(
        WorkItem.sprint_id == sprint_id
    )

    return list(db.scalars(statement).all())