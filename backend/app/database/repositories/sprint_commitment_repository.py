import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sprint_commitment import SprintCommitment
from app.models.work_item import WorkItem


def get_committable_work_items(
    db: Session,
    sprint_id: uuid.UUID
):
    statement = (
        select(WorkItem)
        .where(
            WorkItem.sprint_id == sprint_id,
            WorkItem.work_item_type == "user_story"
        )
        .order_by(WorkItem.created_at)
    )

    return list(db.scalars(statement).all())


def create_commitment_snapshots(
    db: Session,
    sprint_id: uuid.UUID,
    work_items: list[WorkItem]
):
    committed_at = datetime.now(timezone.utc)

    commitments = []

    for item in work_items:
        commitment = SprintCommitment(
            sprint_id=sprint_id,
            work_item_id=item.id,
            committed_story_points=(
                item.story_points
                if item.story_points is not None
                else Decimal("0")
            ),
            committed_at=committed_at
        )

        db.add(commitment)
        commitments.append(commitment)

    return commitments


def get_sprint_commitments(
    db: Session,
    sprint_id: uuid.UUID
):
    statement = (
        select(SprintCommitment)
        .where(SprintCommitment.sprint_id == sprint_id)
        .order_by(
            SprintCommitment.committed_at,
            SprintCommitment.work_item_id
        )
    )

    return list(db.scalars(statement).all())