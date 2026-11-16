import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sprint import Sprint
from app.models.project_team import ProjectTeam


def get_project_team(
    db: Session,
    project_id: uuid.UUID,
    team_id: uuid.UUID
):
    statement = select(ProjectTeam).where(
        ProjectTeam.project_id == project_id,
        ProjectTeam.team_id == team_id
    )
    return db.scalar(statement)


def get_sprint_by_name(
    db: Session,
    project_id: uuid.UUID,
    team_id: uuid.UUID,
    name: str
):
    statement = select(Sprint).where(
        Sprint.project_id == project_id,
        Sprint.team_id == team_id,
        Sprint.name == name
    )
    return db.scalar(statement)


def get_sprints_by_project(
    db: Session,
    project_id: uuid.UUID
):
    statement = (
        select(Sprint)
        .where(Sprint.project_id == project_id)
        .order_by(Sprint.start_date.desc())
    )
    return list(db.scalars(statement).all())


def create_sprint(
    db: Session,
    sprint_data: dict
):
    sprint = Sprint(**sprint_data)
    db.add(sprint)
    db.commit()
    db.refresh(sprint)
    return sprint


def get_sprint_by_id(
    db: Session,
    sprint_id: uuid.UUID
) -> Sprint | None:
    return db.get(Sprint, sprint_id)


def save_sprint(
    db: Session,
    sprint: Sprint
) -> Sprint:
    db.add(sprint)
    db.commit()
    db.refresh(sprint)
    return sprint