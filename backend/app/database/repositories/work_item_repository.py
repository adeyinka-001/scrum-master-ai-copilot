import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.work_item import WorkItem
from app.models.work_item_state_history import WorkItemStateHistory

def get_work_items_by_project(
    db: Session,
    project_id: uuid.UUID
):
    statement = (
        select(WorkItem)
        .where(WorkItem.project_id == project_id)
        .order_by(WorkItem.created_at.desc())
    )

    return list(db.scalars(statement).all())


def create_work_item(
    db: Session,
    work_item_data: dict
):
    work_item = WorkItem(**work_item_data)

    db.add(work_item)
    db.commit()
    db.refresh(work_item)

    return work_item




def get_work_item_by_id(
    db: Session,
    work_item_id: uuid.UUID
) -> WorkItem | None:
    return db.get(WorkItem, work_item_id)


def get_work_item_history(
    db: Session,
    work_item_id: uuid.UUID
):
    statement = (
        select(WorkItemStateHistory)
        .where(
            WorkItemStateHistory.work_item_id == work_item_id
        )
        .order_by(
            WorkItemStateHistory.changed_at.asc()
        )
    )

    return list(db.scalars(statement).all())


def save_work_item(
    db: Session,
    work_item: WorkItem
):
    db.add(work_item)
    db.commit()
    db.refresh(work_item)

    return work_item


def save_work_item_transition(
    db: Session,
    work_item: WorkItem,
    history: WorkItemStateHistory
):
    # Save both records in the same transaction.
    db.add(work_item)
    db.add(history)

    db.commit()
    db.refresh(work_item)

    return work_item