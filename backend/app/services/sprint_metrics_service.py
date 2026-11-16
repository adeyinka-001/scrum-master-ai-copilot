import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.database.repositories import sprint_metrics_repository
from app.schemas.sprint_metrics import SprintMetricsResponse


def calculate_sprint_metrics(
    db: Session,
    sprint_id: uuid.UUID
) -> SprintMetricsResponse:

    sprint = sprint_metrics_repository.get_sprint(
        db,
        sprint_id
    )

    if sprint is None:
        raise HTTPException(
            status_code=404,
            detail="Sprint not found"
        )

    work_items = sprint_metrics_repository.get_sprint_work_items(
        db,
        sprint_id
    )

    total_work_items = len(work_items)

    completed_items = [
        item for item in work_items
        if item.state == "done"
    ]

    completed_work_items = len(completed_items)

    remaining_work_items = (
        total_work_items - completed_work_items
    )

    work_in_progress = sum(
        1 for item in work_items
        if item.state == "in_progress"
    )

    total_story_points = sum(
        float(item.story_points or 0)
        for item in work_items
    )

    completed_story_points = sum(
        float(item.story_points or 0)
        for item in completed_items
    )

    remaining_story_points = (
        total_story_points - completed_story_points
    )

    completion_rate = (
        completed_work_items / total_work_items * 100
        if total_work_items > 0
        else 0.0
    )

    story_point_completion_rate = (
        completed_story_points / total_story_points * 100
        if total_story_points > 0
        else 0.0
    )

    return SprintMetricsResponse(
        sprint_id=sprint.id,
        sprint_name=sprint.name,
        sprint_status=sprint.status,
        start_date=sprint.start_date,
        end_date=sprint.end_date,

        total_work_items=total_work_items,
        completed_work_items=completed_work_items,
        remaining_work_items=remaining_work_items,
        work_in_progress=work_in_progress,

        completion_rate=round(completion_rate, 2),

        total_story_points=round(total_story_points, 2),
        completed_story_points=round(completed_story_points, 2),
        remaining_story_points=round(remaining_story_points, 2),
        story_point_completion_rate=round(
            story_point_completion_rate, 2
        )
    )