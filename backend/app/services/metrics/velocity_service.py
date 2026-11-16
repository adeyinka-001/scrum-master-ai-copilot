import time as timer
from datetime import datetime, time, timedelta, timezone
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import select, func, Date, text
from sqlalchemy.orm import Session

from sqlalchemy import func

from collections import defaultdict
from app.models.project import Project
from app.models.sprint import Sprint
from app.models.sprint_commitment import SprintCommitment
from app.models.work_item import WorkItem
from app.models.work_item_state_history import WorkItemStateHistory
from app.schemas.delivery_velocity import DeliveryVelocityResponse, SprintHistoricalVelocity


def get_historical_velocity(
    db: Session, organization_id: UUID, project_id: UUID, team_id: UUID | None
) -> DeliveryVelocityResponse:

    start_time = timer.perf_counter()
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

    sprint_ids = [sprint.id for sprint in sprints]

    commitment_rows = []

    if sprint_ids:
        commitment_rows = db.execute(
            select(
                SprintCommitment.sprint_id,
                SprintCommitment.work_item_id,
                SprintCommitment.committed_story_points,
            ).where(
                SprintCommitment.sprint_id.in_(sprint_ids)
            )
        ).all()

        # Map each sprint to its historical cutoff.
        sprint_cutoffs = {
            sprint.id: datetime.combine(
                sprint.end_date + timedelta(days=1),
                time.min,
                tzinfo=timezone.utc,
            )
            for sprint in sprints
        }

        # Find the latest state for each committed work item
        # as of the end of its sprint.
        ranked_states = (
            select(
                SprintCommitment.sprint_id.label("sprint_id"),
                SprintCommitment.work_item_id.label("work_item_id"),
                WorkItemStateHistory.new_state.label("state"),
                func.row_number().over(
                    partition_by=(
                        SprintCommitment.sprint_id,
                        SprintCommitment.work_item_id,
                    ),
                    order_by=(
                        WorkItemStateHistory.changed_at.desc(),
                        WorkItemStateHistory.recorded_at.desc(),
                        WorkItemStateHistory.id.desc(),
                    ),
                ).label("rn"),
            )
            .join(
                Sprint,
                Sprint.id == SprintCommitment.sprint_id,
            )
            .join(
                WorkItemStateHistory,
                WorkItemStateHistory.work_item_id
                == SprintCommitment.work_item_id,
            )
            .where(
                SprintCommitment.sprint_id.in_(sprint_ids),
                WorkItemStateHistory.changed_at
                < func.timezone(
                    "UTC",
                    func.cast(Sprint.end_date, Date)
                    + text("INTERVAL '1 day'")
                ),
            )
            .subquery()
        )
        state_rows = db.execute(
            select(
                ranked_states.c.sprint_id,
                ranked_states.c.work_item_id,
                ranked_states.c.state,
            ).where(ranked_states.c.rn == 1)
        ).all()

        state_lookup = {
            (row.sprint_id, row.work_item_id): row.state
            for row in state_rows
        }

    commitments_by_sprint = defaultdict(list)

    for row in commitment_rows:
        commitments_by_sprint[row.sprint_id].append(row)

    rows = []

    for sprint in sprints:
        commitments = commitments_by_sprint[sprint.id]

        if not commitments:
            continue

        committed = completed = unknown = 0.0
        unknown_count = 0

        for commitment in commitments:
            points = float(commitment.committed_story_points)
            committed += points

            state = state_lookup.get(
                (sprint.id, commitment.work_item_id)
            )

            if state is None:
                unknown += points
                unknown_count += 1
            elif state == "done":
                completed += points

        rows.append(
            SprintHistoricalVelocity(
                sprint_id=sprint.id,
                sprint_name=sprint.name,
                start_date=sprint.start_date,
                end_date=sprint.end_date,
                committed_points=round(committed, 2),
                completed_points=round(completed, 2),
                velocity=round(completed, 2),
                predictability=(
                    round(completed / committed * 100, 2)
                    if committed > 0 and unknown_count == 0
                    else None
                ),
                unknown_points=round(unknown, 2),
                unknown_item_count=unknown_count,
            )
        )

    # Incomplete state history means historical velocity is only a lower bound.
    # Do not publish an average as definitive when any sprint has unknown items.
    complete = all(s.unknown_item_count == 0 for s in rows)

    elapsed = timer.perf_counter() - start_time
    print(f"VELOCITY SERVICE EXECUTION TIME: {elapsed:.2f} seconds", flush=True)

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
