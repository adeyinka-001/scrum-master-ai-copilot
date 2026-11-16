import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.project import Project
from app.database.repositories import velocity_repository
from app.schemas.velocity import (
    SprintVelocityResponse,
    ProjectVelocityResponse,
)


def calculate_project_velocity(
    db: Session,
    project_id: uuid.UUID
) -> ProjectVelocityResponse:

    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    sprints = velocity_repository.get_completed_sprints(
        db,
        project_id
    )

    sprint_results = []

    for sprint in sprints:

        commitment_rows = (
            velocity_repository.get_sprint_commitment_details(
                db,
                sprint.id
            )
        )

        # A zero-story sprint can legitimately have an empty snapshot.
        # We will only include sprints with at least one committed story.
        if not commitment_rows:
            continue

        committed_points = sum(
            float(commitment.committed_story_points)
            for commitment, item in commitment_rows
        )

        completed_points = sum(
            float(commitment.committed_story_points)
            for commitment, item in commitment_rows
            if item.state == "done"
        )

        predictability = (
            completed_points / committed_points * 100
            if committed_points > 0
            else 0.0
        )

        sprint_results.append(
            SprintVelocityResponse(
                sprint_id=sprint.id,
                sprint_name=sprint.name,
                start_date=sprint.start_date,
                end_date=sprint.end_date,
                committed_points=round(committed_points, 2),
                completed_points=round(completed_points, 2),
                velocity=round(completed_points, 2),
                predictability=round(predictability, 2)
            )
        )

    sprint_count = len(sprint_results)

    average_velocity = (
        sum(s.velocity for s in sprint_results) / sprint_count
        if sprint_count > 0
        else 0.0
    )

    average_predictability = (
        sum(s.predictability for s in sprint_results) / sprint_count
        if sprint_count > 0
        else 0.0
    )

    return ProjectVelocityResponse(
        project_id=project_id,
        sprint_count=sprint_count,
        average_velocity=round(average_velocity, 2),
        average_predictability=round(average_predictability, 2),
        sprints=sprint_results
    )