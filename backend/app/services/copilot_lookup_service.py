
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.team import Team
from app.models.sprint import Sprint
from app.models.project import Project


def find_teams_by_name(
    db: Session,
    organization_id: UUID,
    team_name: str
):
    """Find teams by name within an organization."""

    statement = (
        select(Team)
        .where(
            Team.organization_id == organization_id,
            func.lower(Team.name) == team_name.strip().lower()
        )
    )

    teams = db.scalars(statement).all()

    return [
        {
            "id": str(team.id),
            "name": team.name,
            "status": team.status
        }
        for team in teams
    ]


def find_sprints_by_name(
    db: Session,
    organization_id: UUID,
    sprint_name: str,
    team_id: UUID | None = None
):
    """Find matching sprints, optionally filtering by team."""

    statement = (
        select(Sprint, Project)
        .join(Project, Sprint.project_id == Project.id)
        .join(Team, Sprint.team_id == Team.id)
        .where(
            Project.organization_id == organization_id,
            Team.organization_id == organization_id,
            func.lower(Sprint.name) == sprint_name.strip().lower()
        )
    )

    if team_id is not None:
        statement = statement.where(
            Sprint.team_id == team_id
        )

    results = db.execute(statement).all()

    return [
        {
            "id": str(sprint.id),
            "name": sprint.name,
            "team_id": str(sprint.team_id),
            "project_id": str(project.id),
            "project_name": project.name,
            "status": sprint.status,
            "start_date": str(sprint.start_date),
            "end_date": str(sprint.end_date)
        }
        for sprint, project in results
    ]


def resolve_sprint_context(
    db: Session,
    organization_id: UUID,
    team_name: str,
    sprint_name: str
):
    """Resolve natural-language team and sprint names."""

    teams = find_teams_by_name(
        db, organization_id, team_name
    )

    if not teams:
        return {
            "status": "not_found",
            "message": f"Team '{team_name}' was not found."
        }

    if len(teams) > 1:
        return {
            "status": "ambiguous",
            "message": "Multiple matching teams were found.",
            "teams": teams
        }

    team = teams[0]

    sprints = find_sprints_by_name(
        db=db,
        organization_id=organization_id,
        sprint_name=sprint_name,
        team_id=UUID(team["id"])
    )

    if not sprints:
        return {
            "status": "not_found",
            "message": (
                f"Sprint '{sprint_name}' was not found "
                f"for team '{team_name}'."
            )
        }

    if len(sprints) > 1:
        return {
            "status": "ambiguous",
            "message": (
                "Multiple matching sprints were found. "
                "Please specify the project."
            ),
            "sprints": sprints
        }

    return {
        "status": "resolved",
        "organization_id": str(organization_id),
        "team": team,
        "sprint": sprints[0]
    }
