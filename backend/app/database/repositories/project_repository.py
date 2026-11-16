import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project

from app.models.organization import Organization

from sqlalchemy.orm import Session

from app.models.project import Project


def get_projects_by_organization(
    db: Session,
    organization_id: uuid.UUID
) -> list[Project]:

    statement = (
        select(Project)
        .where(Project.organization_id == organization_id)
        .order_by(Project.name)
    )

    return list(db.scalars(statement).all())




def get_organization(db: Session, organization_id: uuid.UUID):
    return db.get(Organization, organization_id)


def get_project_by_key(
    db: Session,
    organization_id: uuid.UUID,
    project_key: str
):
    statement = select(Project).where(
        Project.organization_id == organization_id,
        Project.project_key == project_key
    )

    return db.scalar(statement)


def create_project(db: Session, project_data: dict):
    project = Project(**project_data)

    db.add(project)
    db.commit()
    db.refresh(project)

    return project




def get_project_by_id(
    db: Session,
    project_id: uuid.UUID
) -> Project | None:

    return db.get(Project, project_id)


def update_project(
    db: Session,
    project: Project,
    update_data: dict
) -> Project:

    for field, value in update_data.items():
        setattr(project, field, value)

    db.add(project)
    db.commit()
    db.refresh(project)

    return project


def archive_project(
    db: Session,
    project: Project
) -> Project:

    project.status = "archived"

    db.add(project)
    db.commit()
    db.refresh(project)

    return project