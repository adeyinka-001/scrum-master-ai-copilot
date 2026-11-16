from datetime import datetime, time, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.sprint import Sprint
from app.models.sprint_commitment import SprintCommitment
from app.models.work_item import WorkItem
from app.models.work_item_state_history import WorkItemStateHistory
from app.schemas.delivery_velocity import DeliveryVelocityResponse, SprintHistoricalVelocity


def get_historical_velocity(
    db: Session, organization_id: UUID, project_id: UUID, team_id: UUID | None
) -> DeliveryVelocityResponse:
    project = db.scalar(select(Project).where(
        Project.id == project_id, Project.organization_id == organization_id
    ))
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found in organization")

    query = select(Sprint).where(
        Sprint.project_id == project_id, Sprint.status == "completed"
    )
    if team_id is not None:
        query = query.where(Sprint.team_id == team_id)
    sprints = db.scalars(query.order_by(Sprint.end_date, Sprint.id)).all()
    rows = []
    for sprint in sprints:
        # Exclusive UTC midnight after sprint end date. Confirm your business timezone.
        cutoff = datetime.combine(sprint.end_date + timedelta(days=1), time.min, tzinfo=timezone.utc)
        commitments = db.execute(
            select(SprintCommitment, WorkItem)
            .join(WorkItem, SprintCommitment.work_item_id == WorkItem.id)
            .where(SprintCommitment.sprint_id == sprint.id)
        ).all()
        if not commitments:
            continue
        committed = completed = unknown = 0.0
        unknown_count = 0
        for commitment, item in commitments:
            points = float(commitment.committed_story_points)
            committed += points
            # Determine state at cutoff, not the current state.
            # History must be complete to make this conclusive.
            state = db.scalar(
                select(WorkItemStateHistory.new_state)
                .where(WorkItemStateHistory.work_item_id == item.id,
                       WorkItemStateHistory.changed_at < cutoff)
                .order_by(WorkItemStateHistory.changed_at.desc(),
                          WorkItemStateHistory.recorded_at.desc(),
                          WorkItemStateHistory.id.desc())
                .limit(1)
            )
            if state is None:
                # completed_at is a useful fallback ONLY if no subsequent reopen
                # is known; do not assume incomplete history is authoritative.
                unknown += points
                unknown_count += 1
            elif state == "done":
                completed += points
        rows.append(SprintHistoricalVelocity(
            sprint_id=sprint.id, sprint_name=sprint.name,
            start_date=sprint.start_date, end_date=sprint.end_date,
            committed_points=round(committed, 2),
            completed_points=round(completed, 2),
            velocity=round(completed, 2),
            predictability=round(completed / committed * 100, 2)
            if committed > 0 and unknown_count == 0 else None,
            unknown_points=round(unknown, 2),
            unknown_item_count=unknown_count,
        ))

    # Incomplete state history means historical velocity is only a lower bound.
    # Do not publish an average as definitive when any sprint has unknown items.
    complete = all(s.unknown_item_count == 0 for s in rows)
    return DeliveryVelocityResponse(
        project_id=project_id, team_id=team_id, sprint_count=len(rows),
        average_velocity=round(sum(s.velocity for s in rows) / len(rows), 2)
        if rows and complete else None,
        average_predictability=round(
            sum(s.predictability for s in rows if s.predictability is not None) / len(rows), 2
        ) if rows and complete and all(s.predictability is not None for s in rows) else None,
        data_complete=complete,
        note=("Historical results rely on complete state-change history and a UTC sprint-end cutoff. "
              "Unknown items are excluded from completed points; averages are suppressed "
              "when history is incomplete. Commitments are assumed to be the sprint baseline."),
        sprints=rows,
    )
