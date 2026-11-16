from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.project import Project
from app.models.sprint import Sprint
from app.models.team import Team
from app.schemas.dashboard_metrics import DashboardMetricsResponse
from app.schemas.sprint_metrics import SprintMetricsResponse
from app.schemas.velocity import ProjectVelocityResponse
from app.services.dashboard_metrics_service import DashboardMetricsService
from app.services.sprint_metrics_service import calculate_sprint_metrics
from app.services.velocity_service import calculate_project_velocity


router = APIRouter(
    prefix="/metrics",
    tags=["Metrics"]
)

@router.get("/dashboard/teams")
def get_dashboard_teams(
    organization_id: UUID,
    db: Session = Depends(get_db),
):
    teams = db.scalars(
        select(Team)
        .where(Team.organization_id == organization_id)
        .order_by(Team.name)
    ).all()

    return [
        {
            "id": str(team.id),
            "name": team.name,
            "status": team.status,
        }
        for team in teams
    ]

@router.get("/dashboard/sprints")
def get_dashboard_team_sprints(
    organization_id: UUID,
    team_id: UUID,
    db: Session = Depends(get_db),
):
    team = db.scalar(
        select(Team).where(
            Team.id == team_id,
            Team.organization_id == organization_id,
        )
    )

    if team is None:
        raise HTTPException(
            status_code=404,
            detail="Team not found in this organization",
        )

    sprints = db.scalars(
        select(Sprint)
        .join(Project, Sprint.project_id == Project.id)
        .where(
            Sprint.team_id == team_id,
            Project.organization_id == organization_id,
        )
        .order_by(Sprint.start_date.desc())
    ).all()

    return [
        {
            "id": str(sprint.id),
            "name": sprint.name,
            "status": sprint.status,
            "start_date": sprint.start_date,
            "end_date": sprint.end_date,
            "project_id": str(sprint.project_id),
        }
        for sprint in sprints
    ]


@router.get(
    "/sprints/{sprint_id}",
    response_model=SprintMetricsResponse
)
def get_sprint_metrics(
    sprint_id: UUID,
    db: Session = Depends(get_db)
):
    return calculate_sprint_metrics(
        db,
        sprint_id
    )


@router.get(
    "/projects/{project_id}/velocity",
    response_model=ProjectVelocityResponse
)
def get_project_velocity(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    return calculate_project_velocity(
        db,
        project_id
    )

@router.get(
    "/dashboard",
    response_model=DashboardMetricsResponse,
)
def get_dashboard_metrics(
    organization_id: UUID,
    team_id: UUID,
    sprint_id: UUID,
    db: Session = Depends(get_db),
):
    service = DashboardMetricsService(db)

    return service.get_dashboard_metrics(
        organization_id=organization_id,
        team_id=team_id,
        sprint_id=sprint_id,
    )

